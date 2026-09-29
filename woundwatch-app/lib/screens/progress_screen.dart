// The "Progress" tab: the healing dashboard. It draws a wound-area trend line,
// a stacked tissue-composition bar chart, and a healing-estimate card.
//
// IMPORTANT: the numbers here are MOCK for now (see MockData). That's why the
// card shows a "Preview data" badge. When the real DFU pipeline is deployed,
// PhotosProvider.refreshPrediction() will call that API instead of the mock,
// and this screen won't need to change — it just draws whatever prediction it's
// given.
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/healing_prediction.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});

  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  @override
  void initState() {
    super.initState();
    // Load the prediction when the screen first opens, if we don't have one.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final photos = context.read<PhotosProvider>();
      final patient = context.read<AuthProvider>().patient;
      if (photos.prediction == null && patient != null) {
        photos.refreshPrediction(patient.uid);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final photos = context.watch<PhotosProvider>();
    final pred = photos.prediction;

    return Scaffold(
      appBar: AppBar(title: const Text('Progress')),
      body: SafeArea(
        child: photos.isLoading && pred == null
            ? const Center(child: CircularProgressIndicator())
            : pred == null
                ? const _NoPrediction()
                : SingleChildScrollView(
                    padding: const EdgeInsets.all(AppSizes.screenPadding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (pred.isMock) const _PreviewBanner(),
                        const Text('Wound Area',
                            style: TextStyle(
                                fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        _AreaChart(pred: pred),
                        const SizedBox(height: 28),
                        const Text('Tissue Composition',
                            style: TextStyle(
                                fontSize: 18, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 12),
                        _TissueChart(pred: pred),
                        const _TissueLegend(),
                        const SizedBox(height: 28),
                        _PredictionCard(pred: pred),
                      ],
                    ),
                  ),
      ),
    );
  }
}

class _AreaChart extends StatelessWidget {
  final HealingPrediction pred;
  const _AreaChart({required this.pred});

  @override
  Widget build(BuildContext context) {
    final spots = <FlSpot>[
      for (int i = 0; i < pred.daySeries.length; i++)
        FlSpot(pred.daySeries[i].toDouble(), pred.areaSeries[i].toDouble()),
    ];

    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 20, 16, 12),
        child: SizedBox(
          height: 220,
          child: LineChart(
            LineChartData(
              gridData: const FlGridData(show: true, drawVerticalLine: false),
              borderData: FlBorderData(show: false),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                leftTitles: const AxisTitles(
                    sideTitles:
                        SideTitles(showTitles: true, reservedSize: 44)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    interval: 7,
                    getTitlesWidget: (value, meta) => Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text('D${value.toInt()}',
                          style: const TextStyle(
                              fontSize: 11, color: AppColors.textMuted)),
                    ),
                  ),
                ),
              ),
              lineBarsData: [
                LineChartBarData(
                  spots: spots,
                  isCurved: true,
                  color: AppColors.primary,
                  barWidth: 3,
                  dotData: const FlDotData(show: true),
                  belowBarData: BarAreaData(
                    show: true,
                    color: AppColors.primary.withValues(alpha: 0.12),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TissueChart extends StatelessWidget {
  final HealingPrediction pred;
  const _TissueChart({required this.pred});

  @override
  Widget build(BuildContext context) {
    final groups = <BarChartGroupData>[];
    for (int i = 0; i < pred.daySeries.length; i++) {
      final g = pred.granulation[i];
      final s = pred.slough[i];
      final n = pred.necrosis[i];
      // Each bar is one stacked column that should add up to ~100%. The stack
      // items are cumulative ranges: granulation sits 0..g, slough stacks on
      // top of it (g..g+s), necrosis on top of that (g+s..g+s+n).
      groups.add(
        BarChartGroupData(
          x: pred.daySeries[i],
          barRods: [
            BarChartRodData(
              toY: g + s + n,
              width: 18,
              borderRadius: BorderRadius.circular(3),
              rodStackItems: [
                BarChartRodStackItem(0, g, AppColors.granulation),
                BarChartRodStackItem(g, g + s, AppColors.slough),
                BarChartRodStackItem(g + s, g + s + n, AppColors.necrosis),
              ],
            ),
          ],
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 20, 16, 12),
        child: SizedBox(
          height: 220,
          child: BarChart(
            BarChartData(
              maxY: 100,
              gridData: const FlGridData(show: true, drawVerticalLine: false),
              borderData: FlBorderData(show: false),
              titlesData: FlTitlesData(
                topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false)),
                leftTitles: const AxisTitles(
                    sideTitles:
                        SideTitles(showTitles: true, reservedSize: 36)),
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) => Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Text('D${value.toInt()}',
                          style: const TextStyle(
                              fontSize: 11, color: AppColors.textMuted)),
                    ),
                  ),
                ),
              ),
              barGroups: groups,
            ),
          ),
        ),
      ),
    );
  }
}

class _TissueLegend extends StatelessWidget {
  const _TissueLegend();

  Widget _item(Color c, String label) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(width: 12, height: 12, color: c),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      );

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Wrap(
        spacing: 18,
        children: [
          _item(AppColors.granulation, 'Granulation'),
          _item(AppColors.slough, 'Slough'),
          _item(AppColors.necrosis, 'Necrosis'),
        ],
      ),
    );
  }
}

class _PredictionCard extends StatelessWidget {
  final HealingPrediction pred;
  const _PredictionCard({required this.pred});

  @override
  Widget build(BuildContext context) {
    // #25 — with fewer than two real visits a healing score is meaningless.
    if (!pred.enoughVisits) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Healing Prediction',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.hourglass_empty,
                      color: AppColors.healingWatch, size: 22),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text('Waiting for a second visit',
                        style: TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w700)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              const Text(
                'A healing trend needs at least two photos taken on different '
                'days. Take another photo on your next check to see progress.',
                style: TextStyle(color: AppColors.textMuted, height: 1.35),
              ),
            ],
          ),
        ),
      );
    }

    final pct = (pred.healingProbability * 100).round();
    Color color;
    String label;
    if (pred.healingProbability >= 0.7) {
      color = AppColors.healingGood;
      label = 'Likely healing';
    } else if (pred.healingProbability >= 0.5) {
      color = AppColors.healingWatch;
      label = 'Monitor closely';
    } else {
      color = AppColors.healingBad;
      label = 'Consult your doctor';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Healing Prediction',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            // Percentage on top, status label below — stacked so a long label
            // like "Consult your doctor" never overflows the row.
            Text('$pct%',
                style: TextStyle(
                    fontSize: 44,
                    fontWeight: FontWeight.bold,
                    color: color)),
            const SizedBox(height: 8),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(label,
                  style:
                      TextStyle(color: color, fontWeight: FontWeight.bold)),
            ),
            const SizedBox(height: 16),
            const Text('What this is based on:',
                style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            ...pred.topFactors.map((f) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.check_circle,
                          size: 18, color: AppColors.primary),
                      const SizedBox(width: 8),
                      Expanded(child: Text(f)),
                    ],
                  ),
                )),
            const SizedBox(height: 8),
            const Text(
              'This is a wellness estimate, not a medical diagnosis. Always '
              'follow your clinician’s advice.',
              style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textMuted,
                  fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }
}

class _PreviewBanner extends StatelessWidget {
  const _PreviewBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.healingWatch.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline,
              size: 18, color: AppColors.healingWatch),
          const SizedBox(width: 8),
          const Expanded(
            child: Text('Preview data — not a real prediction yet',
                style: TextStyle(fontSize: 12, color: Color(0xFF8A6400))),
          ),
        ],
      ),
    );
  }
}

class _NoPrediction extends StatelessWidget {
  const _NoPrediction();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Text(
          'Progress will appear here once your prediction is ready.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.textMuted),
        ),
      ),
    );
  }
}
