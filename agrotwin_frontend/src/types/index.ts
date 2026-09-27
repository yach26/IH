export interface TwinState {
  fieldId: string;
  crop: string;
  growthStage: string;
  soilHealthScore: number;
  nutrients: {
    n: { current: number; target: number; unit: string };
    p: { current: number; target: number; unit: string };
    k: { current: number; target: number; unit: string };
  };
  currentPlan: {
    nextAction: string;
    quantity: string;
    applicationWindow: string;
    estimatedCost: number;
    confidence: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  activeAlert?: {
    title: string;
    description: string;
  };
}
