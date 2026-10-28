// The "My Photos" tab: every wound photo the patient has taken, newest first,
// grouped into weeks so a long history stays scannable. Tapping a photo opens
// it full-screen with pinch-to-zoom.
import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../models/wound_photo.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';
import '../widgets/wound_image.dart';

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

  Future<void> _confirmDelete(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete this photo?'),
        content: Text(
            'Day ${photo.dayNumber} photo will be permanently removed, and your '
            'healing trend will be recalculated without it. This cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete',
                style: TextStyle(color: AppColors.healingBad)),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    final messenger = ScaffoldMessenger.of(context);
    final done = await context.read<PhotosProvider>().deletePhoto(photo);
    messenger.showSnackBar(SnackBar(
        content: Text(done ? 'Photo deleted' : 'Couldn\'t delete photo')));
  }

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
                child: WoundImage(
                  localPath: photo.localPath,
                  remoteUrl: photo.remoteUrl,
                  size: 84,
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
                        Expanded(
                          child: Text(
                            DateFormat('d MMM, h:mm a').format(photo.timestamp),
                            style: const TextStyle(
                                color: AppColors.textMuted, fontSize: 12),
                          ),
                        ),
                        InkWell(
                          onTap: () => _confirmDelete(context),
                          borderRadius: BorderRadius.circular(20),
                          child: const Padding(
                            padding: EdgeInsets.all(4),
                            child: Icon(Icons.delete_outline,
                                size: 20, color: AppColors.textMuted),
                          ),
                        ),
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
          child: WoundImage(
            localPath: photo.localPath,
            remoteUrl: photo.remoteUrl,
            fit: BoxFit.contain,
          ),
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
