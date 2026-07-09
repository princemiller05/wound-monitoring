// The "My Photos" tab: every wound photo the patient has taken, newest first,
// grouped into weeks so a long history stays scannable. Tapping a photo opens
// it full-screen with pinch-to-zoom.
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/wound_photo.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';

class PhotoHistoryScreen extends StatelessWidget {
  const PhotoHistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final photos = context.watch<PhotosProvider>().photosNewestFirst;

    return Scaffold(
      appBar: AppBar(title: const Text('My Photos')),
      body: SafeArea(
        child: photos.isEmpty
            ? const _EmptyState()
            : _buildGroupedList(context, photos),
      ),
    );
  }

  Widget _buildGroupedList(BuildContext context, List<WoundPhoto> photos) {
    // Bucket photos by week. dayNumber is days since the first photo, so
    // integer-dividing by 7 gives the week index (day 0–6 -> week 1, etc.).
    final Map<int, List<WoundPhoto>> byWeek = {};
    for (final p in photos) {
      final week = (p.dayNumber ~/ 7) + 1;
      byWeek.putIfAbsent(week, () => []).add(p);
    }
    // Show the most recent week at the top.
    final weeks = byWeek.keys.toList()..sort((a, b) => b.compareTo(a));

    return ListView.builder(
      padding: const EdgeInsets.all(AppSizes.screenPadding),
      itemCount: weeks.length,
      itemBuilder: (_, i) {
        final week = weeks[i];
        final items = byWeek[week]!;
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.only(top: 8, bottom: 12),
              child: Text('Week $week',
                  style: const TextStyle(
                      fontSize: 18, fontWeight: FontWeight.bold)),
            ),
            ...items.map((p) => _PhotoTile(photo: p)),
            const SizedBox(height: 8),
          ],
        );
      },
    );
  }
}

class _PhotoTile extends StatelessWidget {
  final WoundPhoto photo;
  const _PhotoTile({required this.photo});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSizes.cardRadius),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => _FullscreenPhoto(photo: photo)),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child: Image.file(
                  File(photo.localPath),
                  width: 84,
                  height: 84,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 84,
                    height: 84,
                    color: AppColors.primaryLight,
                    child: const Icon(Icons.image_not_supported,
                        color: AppColors.primary),
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text('Day ${photo.dayNumber}',
                              style: const TextStyle(
                                  color: AppColors.primary,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 12)),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          DateFormat('d MMM, h:mm a').format(photo.timestamp),
                          style: const TextStyle(
                              color: AppColors.textMuted, fontSize: 12),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Text('Pain ',
                            style: TextStyle(
                                fontSize: 12, color: AppColors.textMuted)),
                        ..._painDots(photo.painLevel),
                      ],
                    ),
                    if (photo.symptoms.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        children: photo.symptoms
                            .map((s) => Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFEFF3F1),
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(s,
                                      style: const TextStyle(fontSize: 11)),
                                ))
                            .toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _painDots(int level) {
    return List.generate(10, (i) {
      final filled = i < level;
      Color c;
      if (level <= 3) {
        c = AppColors.healingGood;
      } else if (level <= 6) {
        c = AppColors.healingWatch;
      } else {
        c = AppColors.healingBad;
      }
      return Container(
        margin: const EdgeInsets.only(right: 3),
        width: 8,
        height: 8,
        decoration: BoxDecoration(
          color: filled ? c : const Color(0xFFD9E2DE),
          shape: BoxShape.circle,
        ),
      );
    });
  }
}

class _FullscreenPhoto extends StatelessWidget {
  final WoundPhoto photo;
  const _FullscreenPhoto({required this.photo});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text('Day ${photo.dayNumber}'),
      ),
      body: Center(
        child: InteractiveViewer(
          minScale: 0.8,
          maxScale: 4,
          child: Image.file(File(photo.localPath)),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.photo_library_outlined,
              size: 64, color: AppColors.textMuted),
          SizedBox(height: 12),
          Text('No photos yet',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          SizedBox(height: 4),
          Text('Take your first wound photo from the Home tab',
              style: TextStyle(color: AppColors.textMuted)),
        ],
      ),
    );
  }
}
