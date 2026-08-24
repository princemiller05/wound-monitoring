import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../models/wound_photo.dart';
import '../providers/auth_provider.dart';
import '../providers/photos_provider.dart';
import '../utils/constants.dart';
import '../theme/app_theme.dart';

/// Import a batch of wound photos the patient has ALREADY taken, labelling each
/// with the real day it was captured (days since the first photo). This is the
/// honest way to backfill an existing photo history — and it makes it easy to
/// show a day-by-day healing trend.
class ImportPhotosScreen extends StatefulWidget {
  const ImportPhotosScreen({super.key});

  @override
  State<ImportPhotosScreen> createState() => _ImportPhotosScreenState();
}

class _ImportEntry {
  final File file;
  int day;
  _ImportEntry(this.file, this.day);
}

class _ImportPhotosScreenState extends State<ImportPhotosScreen> {
  final _picker = ImagePicker();
  final List<_ImportEntry> _entries = [];
  bool _busy = false;

  Future<void> _pick() async {
    final files = await _picker.pickMultiImage(imageQuality: 90);
    if (files.isEmpty) return;
    setState(() {
      for (final f in files) {
        // Suggest a sensible default day (0, 7, 14, …) but let the user fix it
        // to the real capture day.
        _entries.add(_ImportEntry(File(f.path), _entries.length * 7));
      }
    });
  }

  Future<void> _uploadAll() async {
    if (_entries.isEmpty) return;
    final patientId = context.read<AuthProvider>().patient?.uid ?? 'local';
    final photos = _entries
        .map((e) => WoundPhoto(
              id: 'imp-${DateTime.now().microsecondsSinceEpoch}-${e.day}',
              patientId: patientId,
              localPath: e.file.path,
              timestamp: DateTime.now(),
              dayNumber: e.day,
            ))
        .toList();

    setState(() => _busy = true);
    await context.read<PhotosProvider>().importPhotos(photos, patientId);
    if (!mounted) return;
    setState(() => _busy = false);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Photos imported — see Progress')),
    );
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    final status = context.watch<PhotosProvider>().status;

    return Scaffold(
      appBar: AppBar(title: const Text('Import Photos')),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(AppSizes.screenPadding,
                  AppSizes.screenPadding, AppSizes.screenPadding, 8),
              child: Text(
                'Add wound photos you\'ve already taken and set the day each was '
                'captured (days since the first photo). This builds the healing '
                'timeline from your real history.',
                style: AppText.muted,
              ),
            ),
            Expanded(
              child: _entries.isEmpty
                  ? _EmptyState(onPick: _pick)
                  : ListView.separated(
                      padding: const EdgeInsets.all(AppSizes.screenPadding),
                      itemCount: _entries.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 10),
                      itemBuilder: (_, i) => _EntryTile(
                        entry: _entries[i],
                        onDayChanged: (d) =>
                            setState(() => _entries[i].day = d),
                        onRemove: () =>
                            setState(() => _entries.removeAt(i)),
                      ),
                    ),
            ),
            if (status != null && _busy)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 6),
                child: Row(
                  children: [
                    const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2)),
                    const SizedBox(width: 10),
                    Expanded(child: Text(status, style: AppText.muted)),
                  ],
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(AppSizes.screenPadding),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _busy ? null : _pick,
                      icon: const Icon(Icons.add_photo_alternate_outlined),
                      label: Text(_entries.isEmpty ? 'Select photos' : 'Add more'),
                      style: OutlinedButton.styleFrom(
                        minimumSize: const Size.fromHeight(52),
                        side: const BorderSide(color: AppColors.primary),
                        foregroundColor: AppColors.primary,
                      ),
                    ),
                  ),
                  if (_entries.isNotEmpty) ...[
                    const SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _busy ? null : _uploadAll,
                        child: _busy
                            ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                    strokeWidth: 2, color: Colors.white))
                            : Text('Upload ${_entries.length}'),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EntryTile extends StatelessWidget {
  final _ImportEntry entry;
  final ValueChanged<int> onDayChanged;
  final VoidCallback onRemove;

  const _EntryTile({
    required this.entry,
    required this.onDayChanged,
    required this.onRemove,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Image.file(entry.file,
                  width: 64, height: 64, fit: BoxFit.cover),
            ),
            const SizedBox(width: 14),
            const Text('Day', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(width: 10),
            SizedBox(
              width: 64,
              child: TextFormField(
                initialValue: entry.day.toString(),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                textAlign: TextAlign.center,
                decoration: const InputDecoration(
                  isDense: true,
                  contentPadding:
                      EdgeInsets.symmetric(horizontal: 8, vertical: 10),
                ),
                onChanged: (v) => onDayChanged(int.tryParse(v) ?? 0),
              ),
            ),
            const Spacer(),
            IconButton(
              onPressed: onRemove,
              icon: const Icon(Icons.close, color: AppColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final VoidCallback onPick;
  const _EmptyState({required this.onPick});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.collections_outlined,
              size: 64, color: AppColors.textFaint),
          const SizedBox(height: 12),
          const Text('No photos selected',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text('Pick several at once from your gallery',
              style: AppText.muted),
        ],
      ),
    );
  }
}
