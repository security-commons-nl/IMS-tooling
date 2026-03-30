'use client';

import { useState } from 'react';
import useSWR from 'swr';
import { UsersIcon } from '@heroicons/react/24/outline';
import { PageWrapper } from '@/components/layout/page-wrapper';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { EmptyState } from '@/components/ui/empty-state';
import { CardSkeleton } from '@/components/ui/loading-skeleton';
import { useAuth } from '@/providers/auth-provider';
import { api, ApiError } from '@/lib/api-client';
import { formatApiError } from '@/lib/format-error';
import { ROLE_LABELS } from '@/lib/constants';
import type { UserResponse, UserTenantRoleResponse } from '@/lib/api-types';

const ROLE_OPTIONS = [
  { value: '', label: 'Selecteer rol...' },
  ...Object.entries(ROLE_LABELS).map(([value, label]) => ({ value, label })),
];

const DOMAIN_OPTIONS = [
  { value: '', label: 'Geen (alle domeinen)' },
  { value: 'ISMS', label: 'ISMS' },
  { value: 'PIMS', label: 'PIMS' },
  { value: 'BCMS', label: 'BCMS' },
];

export default function GebruikersPage() {
  const { user } = useAuth();
  const tenantId = user?.tenant_id || '';

  const {
    data: users,
    isLoading,
    mutate,
  } = useSWR<UserResponse[]>(
    tenantId ? `/tenants/users/${tenantId}` : null,
    () => api.tenants.listUsers(tenantId),
  );

  const { data: roles, mutate: mutateRoles } = useSWR<UserTenantRoleResponse[]>(
    tenantId ? `/tenants/roles/${tenantId}` : null,
    () => api.tenants.listRoles(tenantId),
  );

  const [showForm, setShowForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    external_id: '',
    role: '',
    domain: '',
  });

  function getRoleForUser(userId: string): UserTenantRoleResponse | undefined {
    return roles?.find((r) => r.user_id === userId);
  }

  function resetForm() {
    setFormData({ name: '', email: '', external_id: '', role: '', domain: '' });
    setFormError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.role) {
      setFormError('Vul naam, email en rol in.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const extId = formData.external_id || `usr-${Date.now()}`;
      const newUser = await api.tenants.createUser({
        name: formData.name,
        email: formData.email,
        external_id: extId,
        tenant_id: tenantId,
      });

      await api.tenants.createRole({
        user_id: newUser.id,
        tenant_id: tenantId,
        role: formData.role,
        domain: formData.domain || null,
      });

      await mutate();
      await mutateRoles();
      setShowForm(false);
      resetForm();
    } catch (err) {
      if (err instanceof ApiError) {
        setFormError(`Fout: ${formatApiError(err.body)}`);
      } else {
        setFormError(`Fout: ${err instanceof Error ? err.message : String(err)}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <PageWrapper
      title="Gebruikersbeheer"
      description="Beheer gebruikers en hun rollen binnen de organisatie."
      actions={
        !showForm ? (
          <Button variant="primary" size="sm" onClick={() => setShowForm(true)}>
            Nieuwe gebruiker
          </Button>
        ) : undefined
      }
    >
      {showForm && (
        <Card className="mb-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="text-base font-semibold text-neutral-900">Nieuwe gebruiker</h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Input
                label="Naam *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Volledige naam"
              />
              <Input
                label="Email *"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="gebruiker@gemeente.nl"
              />
              <Select
                label="Rol *"
                options={ROLE_OPTIONS}
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              />
              <Select
                label="Domein"
                options={DOMAIN_OPTIONS}
                value={formData.domain}
                onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
              />
            </div>
            {formError && <p className="text-sm text-red-600">{formError}</p>}
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={isSubmitting}>
                {isSubmitting ? 'Bezig...' : 'Opslaan'}
              </Button>
              <Button type="button" variant="ghost" size="sm" onClick={() => { setShowForm(false); resetForm(); }}>
                Annuleren
              </Button>
            </div>
          </form>
        </Card>
      )}

      {isLoading && <CardSkeleton />}

      {!isLoading && (!users || users.length === 0) && (
        <Card>
          <EmptyState
            icon={UsersIcon}
            title="Nog geen gebruikers"
            description="Voeg een gebruiker toe om rollen en toegang te beheren."
          />
        </Card>
      )}

      {!isLoading && users && users.length > 0 && (
        <Card padding="none">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-neutral-200 bg-neutral-50">
                  <th className="px-4 py-3 text-left font-medium text-neutral-600">Naam</th>
                  <th className="px-4 py-3 text-left font-medium text-neutral-600">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-neutral-600">Rol</th>
                  <th className="px-4 py-3 text-left font-medium text-neutral-600">Domein</th>
                  <th className="px-4 py-3 text-left font-medium text-neutral-600">Status</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => {
                  const role = getRoleForUser(u.id);
                  return (
                    <tr key={u.id} className="border-b border-neutral-100 hover:bg-neutral-50">
                      <td className="px-4 py-3 font-medium text-neutral-900">{u.name}</td>
                      <td className="px-4 py-3 text-neutral-600">{u.email}</td>
                      <td className="px-4 py-3">
                        {role ? (
                          <Badge variant="primary">
                            {ROLE_LABELS[role.role] || role.role}
                          </Badge>
                        ) : (
                          <span className="text-neutral-400">Geen rol</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {role?.domain ? (
                          <Badge variant="neutral">{role.domain}</Badge>
                        ) : (
                          <span className="text-neutral-400">Alle</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={u.is_active ? 'success' : 'danger'}>
                          {u.is_active ? 'Actief' : 'Inactief'}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </PageWrapper>
  );
}
