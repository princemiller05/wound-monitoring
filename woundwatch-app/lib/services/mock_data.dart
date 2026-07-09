import 'dart:math';
import '../models/healing_prediction.dart';

/// Generates plausible-but-fake healing data so the whole UI can be built and
/// demoed without the real DFU pipeline or any cloud backend.
///
/// Mirrors the mock Azure Function described in the build guide. When the real
/// pipeline is deployed, replace calls to this with an HTTP request that
/// returns the same shape, then build `HealingPrediction.fromMap(...)`.
class MockData {
  MockData._();

  static HealingPrediction predictionFor(String patientId) {
    // Seed by patient so the same patient always gets the same numbers.
    final rng = Random(patientId.hashCode);
    final startArea = 1000 + rng.nextInt(500);
    final days = [0, 7, 14, 21, 28];
    final areas = [
      startArea,
      (startArea * 0.88).round(),
      (startArea * 0.72).round(),
      (startArea * 0.55).round(),
      (startArea * 0.40).round(),
    ];
    final prob = (0.65 + rng.nextDouble() * 0.20);

    return HealingPrediction(
      healingProbability: double.parse(prob.toStringAsFixed(2)),
      predictedLabel: prob > 0.5 ? 'healing' : 'non_healing',
      topFactors: const [
        'Granulation tissue increasing',
        'Wound area reducing steadily',
        'Low necrosis percentage',
      ],
      daySeries: days,
      areaSeries: areas,
      granulation: const [30, 45, 55, 65, 72],
      slough: const [50, 40, 30, 25, 20],
      necrosis: const [20, 15, 15, 10, 8],
      isMock: true,
    );
  }
}
