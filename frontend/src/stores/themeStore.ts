import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "travel" | "agency" | "agent";
type ComponentVariant = "v1" | "v2" | "travel" | "agency" | "agent";

interface ThemeState {
  // Current theme
  currentTheme: Theme;
  setTheme: (theme: Theme) => void;

  // Component variants
  componentVariants: Record<string, ComponentVariant>;
  setComponentVariant: (component: string, variant: ComponentVariant) => void;
  resetVariants: () => void;

  // Debug mode
  debugMode: boolean;
  setDebugMode: (enabled: boolean) => void;

  // UI density
  density: "compact" | "normal" | "comfortable";
  setDensity: (density: "compact" | "normal" | "comfortable") => void;
}

const defaultVariants: Record<string, ComponentVariant> = {
  Shell: "v2",
  Workbench: "v2",
  DataCard: "v2",
  IntakeTab: "v2",
  PacketTab: "v2",
  DecisionTab: "v2",
  StrategyTab: "v2",
  SafetyTab: "v2",
  RouteMap: "travel",
  PipelineFlow: "agency",
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      currentTheme: "agency",
      componentVariants: defaultVariants,
      debugMode: false,
      density: "normal",

      setTheme: (theme) => {
        set({ currentTheme: theme });
      },

      setComponentVariant: (component, variant) => {
        set((state) => ({
          componentVariants: {
            ...state.componentVariants,
            [component]: variant,
          },
        }));
      },

      resetVariants: () => {
        set({ componentVariants: defaultVariants });
      },

      setDebugMode: (enabled) => set({ debugMode: enabled }),
      setDensity: (density) => set({ density }),
    }),
    {
      name: "travel-agency-theme",
      partialize: (state) => ({
        currentTheme: state.currentTheme,
        componentVariants: state.componentVariants,
        density: state.density,
      }),
    }
  )
);

// Hook for getting current variant
export function useComponentVariant(component: string): ComponentVariant {
  return useThemeStore((state) => state.componentVariants[component] || "v2");
}
