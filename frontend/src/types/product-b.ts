export interface ProductBKpiScope {
  type: 'agency' | 'global';
  workspace_id: string | null;
  workspace_count: number;
}

export interface ProductBKpiResponse {
  scope: ProductBKpiScope;
  window_days: number;
  qualified_only: boolean;
  sample: Record<string, unknown>;
  kpis: {
    time_to_first_credible_finding_ms?: {
      p50: number | null;
      p90: number | null;
      n: number;
    };
    forward_without_edit_rate?: number | null;
    agency_revision_rate_observed_7d?: number | null;
    inferred_revision_rate?: number | null;
    dark_funnel_rate?: number | null;
    product_a_pull_through?: number | null;
    [key: string]: unknown;
  };
  confidence_tiers: Record<string, number>;
  counts: Record<string, number>;
  definitions: Record<string, unknown>;
  provenance: {
    data_source: string;
    generated_at: string;
  };
}
