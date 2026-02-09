# Chat Island Voice Upgrade

## Context

De Chat Island (`frontend/ims/components/chat_island.py`) is een floating chat panel rechtsonder waarmee gebruikers met AI agents praten. Momenteel alleen via tekst. Deze upgrade voegt spraak-input toe via de browser-native Web Speech API.

**Geen backend-wijzigingen nodig** — spraak wordt client-side omgezet naar tekst en gaat als regulier bericht naar de bestaande agent API.

## Flow

```
Gebruiker spreekt
    -> Web Speech API (browser, client-side)
    -> tekst in ChatState.current_input
    -> ChatState.send_message()
    -> bestaande agent API
    -> tekstueel antwoord
```

EU data sovereignty: spraakherkenning draait volledig in de browser, geen externe diensten.

## Bestanden te wijzigen

| # | Bestand | Wijziging |
|---|---------|-----------|
| 1 | `frontend/ims/state/chat.py` | Voice state + JS interop |
| 2 | `frontend/ims/components/chat_island.py` | Microfoon-knop in input area |
| 3 | `frontend/assets/custom.css` | Pulse animatie tijdens opname |

## 1. State (`frontend/ims/state/chat.py`)

### Nieuwe state variabelen:
```python
is_recording: bool = False
voice_supported: bool = True   # False als browser geen Web Speech API heeft
voice_error: str = ""
```

### Nieuwe methoden:

**`toggle_recording()`** — Start/stop spraakherkenning via `rx.call_script()`:
```python
def toggle_recording(self):
    self.is_recording = not self.is_recording
    if self.is_recording:
        return rx.call_script("""
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                // Browser ondersteunt het niet
                return;
            }
            const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
            window._ims_recognition = new SR();
            window._ims_recognition.lang = 'nl-NL';
            window._ims_recognition.continuous = false;
            window._ims_recognition.interimResults = false;

            window._ims_recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                // Zet tekst in het input veld en verstuur
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                const input = document.getElementById('chat-input');
                if (input) {
                    nativeInputValueSetter.call(input, transcript);
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
            };

            window._ims_recognition.onend = () => {
                // Wordt opgepikt door de volgende toggle_recording call
            };

            window._ims_recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
            };

            window._ims_recognition.start();
        """)
    else:
        return rx.call_script("""
            if (window._ims_recognition) {
                window._ims_recognition.stop();
            }
        """)
```

**`check_voice_support()`** — Eenmalig bij chat open:
```python
def check_voice_support(self):
    return rx.call_script(
        "!!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)"
    )
```

## 2. UI (`frontend/ims/components/chat_island.py`)

### Wijzig `chat_input()`:

Voeg microfoon-knop toe **links van** de send-knop:

```python
def chat_input() -> rx.Component:
    return rx.hstack(
        rx.input(
            id="chat-input",
            placeholder="Stel een vraag...",
            value=ChatState.current_input,
            on_change=ChatState.set_input,
            on_key_down=lambda key: rx.cond(
                key == "Enter",
                ChatState.send_message(),
                None,
            ),
            flex="1",
            size="2",
            auto_focus=True,
        ),
        # Microfoon knop
        rx.icon_button(
            rx.icon(
                rx.cond(ChatState.is_recording, "mic-off", "mic"),
                size=18,
            ),
            on_click=ChatState.toggle_recording,
            size="2",
            variant=rx.cond(ChatState.is_recording, "solid", "ghost"),
            color_scheme=rx.cond(ChatState.is_recording, "red", "gray"),
            class_name=rx.cond(ChatState.is_recording, "voice-recording", ""),
        ),
        # Send knop
        rx.icon_button(
            rx.icon("send", size=18),
            on_click=ChatState.send_message,
            disabled=ChatState.is_loading,
            size="2",
        ),
        width="100%",
        spacing="2",
    )
```

Visueel:
```
[ Stel een vraag...              ] [mic] [send]
```

Tijdens opname:
```
[ Stel een vraag...              ] [mic-off (rood, pulserend)] [send]
```

## 3. CSS (`frontend/assets/custom.css`)

```css
/* Voice recording pulse animatie */
@keyframes voice-pulse {
    0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
    70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.voice-recording {
    animation: voice-pulse 1.5s infinite;
}
```

## Verificatie

1. Open de Chat Island (klik op message-circle rechtsonder)
2. Klik op het microfoon-icoon
3. Spreek een vraag in (Nederlands)
4. Tekst verschijnt in het inputveld
5. Klik op send (of auto-send na herkenning)
6. AI agent beantwoordt normaal

## Browser Support

| Browser | Support |
|---------|---------|
| Chrome / Edge | Volledig (beste kwaliteit) |
| Safari | Volledig |
| Firefox | Beperkt (geen `webkitSpeechRecognition`) |

Fallback: als `SpeechRecognition` niet beschikbaar is, wordt de microfoon-knop verborgen (`voice_supported = false`).

## Toekomstige uitbreidingen

1. **Auto-send**: Na spraakherkenning automatisch versturen (ipv handmatig send klikken)
2. **Interim results**: Live tekst tonen terwijl gebruiker spreekt
3. **Taal-detectie**: Automatisch schakelen tussen NL/EN
4. **Voice response**: Text-to-speech voor agent-antwoorden (Web Speech Synthesis API)
