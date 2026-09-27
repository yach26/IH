export type GrowthStage = string;

export interface CropVisualState {
  stage: GrowthStage;
  stageProgress: number; // 0.0 to 1.0 within the stage
  vigor: 'Poor' | 'Moderate' | 'Good' | 'Excellent';
  leafCondition: 'Healthy' | 'Reduced Greenness' | 'Drooping' | 'Wilted' | 'Yellowing';
  waterStress: 'Low' | 'Moderate' | 'High' | 'Severe';
  nutrientStress: 'Low' | 'Moderate' | 'High' | 'Severe';
  overallState: 'Healthy' | 'Mild Stress' | 'Moderate Stress' | 'High Stress';
  explanation: string;
}

export interface SimulationInput {
  cropId: string;
  fertilizer: number; // 0-150 kg/ha
  rainfallChange: number; // -50 to 50 (%)
  irrigation: 'Low' | 'Normal' | 'High';
  applicationTiming: 'Early' | 'On time' | 'Delayed';
  plantingShift: number; // -30 to 30 days
}

export interface CropConfig {
  id: string;
  name: string;
  icon: string;
  has3D: boolean;
  sketchfabId?: string;
  sketchfabTitle?: string;
  currentStageDesc?: string;
  stages: GrowthStage[];
  baselineFertilizer: number; // kg/ha
  fertilizerRange: [number, number]; // [min, max] for optimal
  stageDurations: number[]; // days for each stage
}
