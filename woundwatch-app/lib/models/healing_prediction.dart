/// The healing prediction returned by the DFU pipeline.
///
/// In this phase the data is generated locally (mock). The field names match
/// the real pipeline's response schema, so swapping in the live API later is
/// just a matter of changing where this object is built from.
class HealingPrediction {
  final double healingProbability; // 0.0–1.0
  final String predictedLabel; // "healing" | "non_healing"
  final List<String> topFactors;
  final List<int> daySeries; // x-axis, e.g. [0, 7, 14, 21, 28]
  final List<int> areaSeries; // wound area per day
  final List<double> granulation; // % per day
  final List<double> slough;
  final List<double> necrosis;
  final bool isMock;

  /// #25 — a healing score from a single photo is meaningless. When there's
  /// only one visit, [enoughVisits] is false and the UI shows "waiting for
  /// second visit" instead of a percentage.
  final bool enoughVisits;
  final int visits;

  HealingPrediction({
    required this.healingProbability,
    required this.predictedLabel,
    required this.topFactors,
    required this.daySeries,
    required this.areaSeries,
    required this.granulation,
    required this.slough,
    required this.necrosis,
    this.isMock = true,
    this.enoughVisits = true,
    this.visits = 0,
  });

  factory HealingPrediction.fromMap(Map<String, dynamic> map) {
    final tissue = (map['tissue_series'] as Map?) ?? const {};
    List<double> toD(dynamic l) =>
        (l as List?)?.map((e) => (e as num).toDouble()).toList() ?? const [];
    List<int> toI(dynamic l) =>
        (l as List?)?.map((e) => (e as num).toInt()).toList() ?? const [];

    return HealingPrediction(
      healingProbability: (map['healing_probability'] as num).toDouble(),
      predictedLabel: map['predicted_label'] as String? ?? 'healing',
      topFactors: (map['top_factors'] as List?)?.cast<String>() ?? const [],
      daySeries: toI(map['day_series']),
      areaSeries: toI(map['area_series']),
      granulation: toD(tissue['granulation']),
      slough: toD(tissue['slough']),
      necrosis: toD(tissue['necrosis']),
      isMock: map['is_mock'] as bool? ?? false,
    );
  }
}
