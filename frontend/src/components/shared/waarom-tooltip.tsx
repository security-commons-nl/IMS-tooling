import { Tooltip } from '@/components/ui/tooltip';
import { QuestionMarkCircleIcon } from '@heroicons/react/24/outline';

interface WaaromTooltipProps {
  text: string;
}

export function WaaromTooltip({ text }: WaaromTooltipProps) {
  return (
    <Tooltip content={text} position="right">
      <button
        type="button"
        className="inline-flex items-center justify-center rounded-full p-0.5 text-neutral-400 hover:text-neutral-600 transition-colors"
        aria-label="Toelichting"
      >
        <QuestionMarkCircleIcon className="h-4 w-4" />
      </button>
    </Tooltip>
  );
}
