import type {
  CreateSeasonalCampaignRequest,
  SeasonalCampaign,
  UpdateSeasonalCampaignRequest,
} from '@/lib/api-client';

type CampaignStatus = Exclude<SeasonalCampaign['status'], undefined>;

export const CAMPAIGN_CHANNELS = ['organic', 'email', 'social', 'paid'] as const;

export type CampaignChannel = (typeof CAMPAIGN_CHANNELS)[number];

export interface CampaignFormState {
  name: string;
  status: SeasonalCampaign['status'];
  destination: string;
  campaign_window_start_month: string;
  campaign_window_end_month: string;
  target_budget_min: string;
  target_budget_max: string;
  notes: string;
  blocklist: string;
  channel_mix: Record<string, string>;
}

function toCampaignStatus(status: CampaignStatus | undefined = 'draft'): CampaignStatus {
  if (status === 'active' || status === 'paused' || status === 'archived') {
    return status;
  }

  return 'draft';
}

export function defaultChannelMix(record?: Record<string, number>): Record<string, string> {
  return CAMPAIGN_CHANNELS.reduce<Record<string, string>>((acc, channel) => {
    if (record && typeof record[channel] === 'number') {
      acc[channel] = String(record[channel]);
    } else {
      acc[channel] = '0';
    }
    return acc;
  }, {});
}

export function makeEmptyCampaignForm(): CampaignFormState {
  return {
    name: '',
    status: 'draft',
    destination: '',
    campaign_window_start_month: '',
    campaign_window_end_month: '',
    target_budget_min: '',
    target_budget_max: '',
    notes: '',
    blocklist: '',
    channel_mix: defaultChannelMix(),
  };
}

export function campaignFormFromPlan(plan: SeasonalCampaign): CampaignFormState {
  return {
    name: plan.name,
    status: toCampaignStatus(plan.status),
    destination: plan.destination ?? '',
    campaign_window_start_month: plan.campaign_window_start_month ? String(plan.campaign_window_start_month) : '',
    campaign_window_end_month: plan.campaign_window_end_month ? String(plan.campaign_window_end_month) : '',
    target_budget_min: plan.target_budget_min == null ? '' : String(plan.target_budget_min),
    target_budget_max: plan.target_budget_max == null ? '' : String(plan.target_budget_max),
    notes: plan.notes ?? '',
    blocklist: plan.blocklist.join('\n'),
    channel_mix: defaultChannelMix(plan.channel_mix),
  };
}

export function parseNumericValue(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const numberValue = Number(value);
  return Number.isFinite(numberValue) ? numberValue : undefined;
}

export function parseIntValue(value: string): number | undefined {
  if (!value.trim()) return undefined;
  const numberValue = Number(value);
  return Number.isInteger(numberValue) && Number.isFinite(numberValue) ? numberValue : undefined;
}

export function parseNumericValueForFormUpdate(value: string): number | null | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const numberValue = Number(trimmed);
  if (!Number.isFinite(numberValue)) {
    return undefined;
  }

  return numberValue;
}

export function parseIntValueForFormUpdate(value: string): number | null | undefined {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const numberValue = parseIntValue(trimmed);
  return numberValue;
}

export function parseChannelMix(valueByChannel: Record<string, string>): Record<string, number> {
  const result: Record<string, number> = {};
  CAMPAIGN_CHANNELS.forEach((channel) => {
    const parsed = parseNumericValue(valueByChannel[channel]);
    if (parsed !== undefined) {
      result[channel] = parsed;
    }
  });
  return result;
}

export function parseBlocklist(raw: string): string[] {
  return raw
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);
}

export function toCreateCampaignPayload(form: CampaignFormState): CreateSeasonalCampaignRequest {
  return {
    name: form.name.trim(),
    status: form.status,
    destination: form.destination.trim() || undefined,
    campaign_window_start_month: parseIntValue(form.campaign_window_start_month),
    campaign_window_end_month: parseIntValue(form.campaign_window_end_month),
    channel_mix: parseChannelMix(form.channel_mix),
    target_budget_min: parseNumericValue(form.target_budget_min),
    target_budget_max: parseNumericValue(form.target_budget_max),
    notes: form.notes.trim() || undefined,
    blocklist: parseBlocklist(form.blocklist),
  };
}

function parseFormString(value: string): string {
  return value.trim();
}

function isSameMonthField(formValue: string, modelValue: number | null | undefined): boolean {
  return parseFormString(formValue) === parseFormString(modelValue == null ? '' : String(modelValue));
}

export function toUpdateCampaignPayload(
  form: CampaignFormState,
  original: SeasonalCampaign,
): UpdateSeasonalCampaignRequest {
  const payload: UpdateSeasonalCampaignRequest = {};

  const trimmedName = parseFormString(form.name);
  if (trimmedName && trimmedName !== original.name) {
    payload.name = trimmedName;
  }

  if (form.status !== original.status) {
    payload.status = form.status;
  }

  const destinationValue = parseFormString(form.destination);
  const originalDestination = original.destination ?? '';
  if (destinationValue !== originalDestination) {
    payload.destination = destinationValue || null;
  }

  const startMonthValue = parseNumericValueForFormUpdate(form.campaign_window_start_month);
  if (!isSameMonthField(form.campaign_window_start_month, original.campaign_window_start_month)) {
    payload.campaign_window_start_month = startMonthValue;
  }

  const endMonthValue = parseNumericValueForFormUpdate(form.campaign_window_end_month);
  if (!isSameMonthField(form.campaign_window_end_month, original.campaign_window_end_month)) {
    payload.campaign_window_end_month = endMonthValue;
  }

  const minBudgetValue = parseNumericValueForFormUpdate(form.target_budget_min);
  if (parseFormString(form.target_budget_min) !== parseFormString(original.target_budget_min)) {
    payload.target_budget_min = minBudgetValue;
  }

  const maxBudgetValue = parseNumericValueForFormUpdate(form.target_budget_max);
  if (parseFormString(form.target_budget_max) !== parseFormString(original.target_budget_max)) {
    payload.target_budget_max = maxBudgetValue;
  }

  const notesValue = parseFormString(form.notes);
  if (notesValue !== parseFormString(original.notes ?? '')) {
    payload.notes = notesValue || null;
  }

  const blocklistValue = parseBlocklist(form.blocklist);
  if (JSON.stringify(blocklistValue) !== JSON.stringify(original.blocklist)) {
    payload.blocklist = blocklistValue;
  }

  const channelMixValue = parseChannelMix(form.channel_mix);
  if (JSON.stringify(channelMixValue) !== JSON.stringify(original.channel_mix)) {
    payload.channel_mix = channelMixValue;
  }

  return payload;
}
