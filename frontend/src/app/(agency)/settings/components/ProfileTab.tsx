'use client';

import { Building2, Mail, Phone, Globe, ImageIcon, Sparkles, BadgeCheck, Info } from 'lucide-react';
import type { AgencySettings } from '@/hooks/useAgencySettings';

interface ProfileTabProps {
  draft: AgencySettings;
  onChange: (updater: (prev: AgencySettings) => AgencySettings) => void;
}

function Field({
  label,
  icon: Icon,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  value: string;
  onChange: (val: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div className="space-y-1.5">
      <label className="flex items-center gap-1.5 text-ui-xs font-medium text-[#8b949e]">
        <Icon className="size-3.5" />
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-sm text-[#e6edf3] placeholder:text-[#484f58] focus:outline-none focus:border-[#58a6ff] transition-colors"
      />
    </div>
  );
}

export function ProfileTab({ draft, onChange }: ProfileTabProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-ui-sm font-semibold text-[#e6edf3]">Agency Profile</h2>
        <p className="text-ui-xs text-[#8b949e] mt-1">
          This information appears on quotes, emails, and the traveler-facing portal.
        </p>
      </div>

      <section className="rounded-lg border border-[#30363d] bg-[#161b22] p-4 space-y-3">
        <div className="flex items-center gap-2">
          <h3 className="text-ui-sm font-semibold text-[#e6edf3]">Brand & Plan Identity</h3>
          <span
            title="Use these fields to separate product identity from agency identity so naming stays consistent across internal and customer-facing surfaces."
            className="inline-flex items-center justify-center text-[#8b949e] hover:text-[#c9d1d9] cursor-help"
            aria-label="Brand and plan identity help"
          >
            <Info className="size-3.5" />
          </span>
        </div>
        <p className="text-ui-xs text-[#8b949e]">
          Waypoint OS stays the product name. Configure agency identity below so labels never feel random or inconsistent.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
          <div className="rounded-md border border-[#30363d] bg-[#0d1117] p-2.5">
            <p className="text-[11px] uppercase tracking-wide text-[#8b949e]">Agency Name</p>
            <p className="mt-1 text-ui-xs text-[#c9d1d9]">Primary workspace identity (sidebar, settings, internal ownership context).</p>
          </div>
          <div className="rounded-md border border-[#30363d] bg-[#0d1117] p-2.5">
            <p className="text-[11px] uppercase tracking-wide text-[#8b949e]">Sub-brand (Optional)</p>
            <p className="mt-1 text-ui-xs text-[#c9d1d9]">Commercial flavor or line of business (for example luxury, adventure, destination-specific unit).</p>
          </div>
          <div className="rounded-md border border-[#30363d] bg-[#0d1117] p-2.5">
            <p className="text-[11px] uppercase tracking-wide text-[#8b949e]">Plan Label (Optional)</p>
            <p className="mt-1 text-ui-xs text-[#c9d1d9]">Commercial package/tier naming (for example Growth, Pro, Enterprise service envelope).</p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Field
          label="Agency Name"
          icon={Building2}
          value={draft.profile.agency_name}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.agency_name = v;
              return prev;
            })
          }
          placeholder="e.g., Bali Bliss Travels"
        />

        <Field
          label="Sub-brand (Optional)"
          icon={Sparkles}
          value={draft.profile.sub_brand}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.sub_brand = v;
              return prev;
            })
          }
          placeholder="e.g., Luxury Journeys"
        />

        <Field
          label="Plan Label (Optional)"
          icon={BadgeCheck}
          value={draft.profile.plan_label}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.plan_label = v;
              return prev;
            })
          }
          placeholder="e.g., Growth Plan"
        />

        <Field
          label="Contact Email"
          icon={Mail}
          type="email"
          value={draft.profile.contact_email}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.contact_email = v;
              return prev;
            })
          }
          placeholder="hello@youragency.com"
        />

        <Field
          label="Contact Phone"
          icon={Phone}
          type="tel"
          value={draft.profile.contact_phone}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.contact_phone = v;
              return prev;
            })
          }
          placeholder="+91 99999 99999"
        />

        <Field
          label="Website"
          icon={Globe}
          type="url"
          value={draft.profile.website}
          onChange={(v) =>
            onChange((prev) => {
              prev.profile.website = v;
              return prev;
            })
          }
          placeholder="https://youragency.com"
        />

        <div className="md:col-span-2">
          <Field
            label="Logo URL"
            icon={ImageIcon}
            type="url"
            value={draft.profile.logo_url}
            onChange={(v) =>
              onChange((prev) => {
                prev.profile.logo_url = v;
                return prev;
              })
            }
            placeholder="https://youragency.com/logo.png"
          />
        </div>
      </div>

      {/* Preview */}
      {draft.profile.agency_name && (
        <div className="rounded-lg border border-[#30363d] bg-[#161b22] p-4 space-y-2">
          <p className="text-ui-xs font-medium text-[#8b949e] uppercase tracking-wide">Preview</p>
          <div className="flex items-center gap-3">
            {draft.profile.logo_url ? (
              <div
                aria-label={`${draft.profile.agency_name} logo`}
                role="img"
                className="size-10 rounded-lg border border-[#30363d] bg-gradient-to-br from-[#2563eb] to-[#39d0d8] bg-cover bg-center"
                style={{ backgroundImage: `url("${draft.profile.logo_url}")` }}
              />
            ) : (
              <div className="size-10 rounded-lg bg-gradient-to-br from-[#2563eb] to-[#39d0d8] flex items-center justify-center text-white text-ui-xs font-bold">
                {draft.profile.agency_name.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div>
              <p className="text-ui-sm font-medium text-[#e6edf3]">{draft.profile.agency_name}</p>
              {(draft.profile.sub_brand || draft.profile.plan_label) && (
                <p className="text-ui-xs text-[#8b949e]">
                  {[draft.profile.sub_brand, draft.profile.plan_label].filter(Boolean).join(' · ')}
                </p>
              )}
              {draft.profile.contact_email && (
                <p className="text-ui-xs text-[#8b949e]">{draft.profile.contact_email}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
