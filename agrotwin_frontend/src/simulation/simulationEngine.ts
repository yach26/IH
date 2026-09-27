import { SimulationInput, CropVisualState } from './types';
import { CROPS } from './cropConfigs';

export function simulateCrop(input: SimulationInput): CropVisualState {
  const config = CROPS[input.cropId.toLowerCase()] || CROPS['rice'];
  
  // Calculate total days simulated based on planting shift (simplistic mapping for demo)
  // Let's assume the simulation "looks" at a point halfway through the crop's life by default,
  // shifted by the planting date shift.
  const totalDuration = config.stageDurations.reduce((a, b) => a + b, 0);
  let simulatedDay = (totalDuration / 2) + input.plantingShift;
  
  // Bound the day
  simulatedDay = Math.max(0, Math.min(simulatedDay, totalDuration));
  
  // Determine stage
  let stageIdx = 0;
  let daysAccumulated = 0;
  for (let i = 0; i < config.stageDurations.length; i++) {
    if (simulatedDay <= daysAccumulated + config.stageDurations[i]) {
      stageIdx = i;
      break;
    }
    daysAccumulated += config.stageDurations[i];
  }
  
  const currentStage = config.stages[stageIdx];
  const stageDuration = config.stageDurations[stageIdx];
  const daysInStage = simulatedDay - daysAccumulated;
  const stageProgress = stageDuration > 0 ? daysInStage / stageDuration : 1;

  // Evaluate Nutrient Stress
  let nutrientStress: CropVisualState['nutrientStress'] = 'Low';
  let nutrientScore = 0; // Negative means stress

  if (input.fertilizer < config.fertilizerRange[0]) {
    const deficit = config.fertilizerRange[0] - input.fertilizer;
    if (deficit > 30) nutrientStress = 'Severe';
    else if (deficit > 15) nutrientStress = 'High';
    else nutrientStress = 'Moderate';
    nutrientScore = -deficit;
  } else if (input.fertilizer > config.fertilizerRange[1]) {
    // Excess fertilizer doesn't necessarily improve health indefinitely, might cause slight issues
    nutrientStress = 'Moderate'; 
    nutrientScore = -5; // Slight penalty for over-fertilization
  }

  if (input.applicationTiming === 'Delayed') {
    nutrientScore -= 10;
    if (nutrientStress === 'Low') nutrientStress = 'Moderate';
    else if (nutrientStress === 'Moderate') nutrientStress = 'High';
  } else if (input.applicationTiming === 'Early') {
    nutrientScore -= 5;
  }

  // Evaluate Water Stress
  let waterStress: CropVisualState['waterStress'] = 'Low';
  let waterScore = 0;

  if (input.rainfallChange < -20) {
    if (input.irrigation === 'Low') {
      waterStress = 'Severe';
      waterScore = -30;
    } else if (input.irrigation === 'Normal') {
      waterStress = 'High';
      waterScore = -15;
    } else {
      waterStress = 'Moderate';
      waterScore = -5;
    }
  } else if (input.rainfallChange < 0) {
    if (input.irrigation === 'Low') {
      waterStress = 'High';
      waterScore = -15;
    } else if (input.irrigation === 'Normal') {
      waterStress = 'Moderate';
      waterScore = -5;
    }
  } else if (input.rainfallChange > 30) {
     if (input.irrigation === 'High') {
         waterStress = 'High'; // Waterlogging
         waterScore = -15;
     } else {
         waterStress = 'Moderate';
         waterScore = -5;
     }
  } else {
     // Normal rainfall
     if (input.irrigation === 'High') {
         waterStress = 'Moderate'; // Slight overwatering
         waterScore = -5;
     }
  }

  // Determine Overall State, Vigor, and Leaf Condition
  const totalScore = nutrientScore + waterScore;
  let overallState: CropVisualState['overallState'] = 'Healthy';
  let vigor: CropVisualState['vigor'] = 'Good';
  let leafCondition: CropVisualState['leafCondition'] = 'Healthy';

  if (totalScore < -30) {
    overallState = 'High Stress';
    vigor = 'Poor';
    leafCondition = 'Wilted';
  } else if (totalScore < -15) {
    overallState = 'Moderate Stress';
    vigor = 'Moderate';
    leafCondition = nutrientScore < waterScore ? 'Yellowing' : 'Drooping';
  } else if (totalScore < -5) {
    overallState = 'Mild Stress';
    vigor = 'Good';
    leafCondition = 'Reduced Greenness';
  } else {
    overallState = 'Healthy';
    vigor = 'Excellent';
    leafCondition = 'Healthy';
  }
  
  // Ensure we don't have excellent vigor with high stress
  if (waterStress === 'Severe' || nutrientStress === 'Severe') {
      overallState = 'High Stress';
      vigor = 'Poor';
  }

  // Generate deterministic explanation
  let explanation = '';
  
  if (overallState === 'Healthy') {
      explanation = 'Baseline conditions applied. No significant stress detected; crop is developing normally.';
  } else {
      const issues = [];
      if (input.fertilizer < config.fertilizerRange[0]) issues.push('reduced nitrogen');
      else if (input.fertilizer > config.fertilizerRange[1]) issues.push('excess nitrogen');
      
      if (input.rainfallChange < -10) issues.push('reduced rainfall');
      else if (input.rainfallChange > 20) issues.push('excessive rainfall');
      
      if (input.irrigation === 'Low' && input.rainfallChange <= 0) issues.push('insufficient irrigation');
      if (input.irrigation === 'High' && input.rainfallChange >= 0) issues.push('over-irrigation');
      
      if (input.applicationTiming === 'Delayed') issues.push('delayed fertilizer application');
      
      const issueStr = issues.length > 0 ? issues.join(' and ') : 'sub-optimal conditions';
      
      explanation = `Due to ${issueStr}, the simulated crop shows `;
      
      const impacts = [];
      if (vigor === 'Poor' || vigor === 'Moderate') impacts.push('lower vigor');
      if (nutrientStress === 'Moderate' || nutrientStress === 'High' || nutrientStress === 'Severe') impacts.push('increased nutrient stress');
      if (waterStress === 'Moderate' || waterStress === 'High' || waterStress === 'Severe') impacts.push('increased water stress');
      
      if (impacts.length > 0) {
          explanation += impacts.join(' and ') + '.';
      } else {
          explanation += 'minor stress signs.';
      }
  }

  return {
    stage: currentStage,
    stageProgress,
    vigor,
    leafCondition,
    waterStress,
    nutrientStress,
    overallState,
    explanation
  };
}
