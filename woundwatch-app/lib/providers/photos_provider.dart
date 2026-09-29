import 'dart:io';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/wound_photo.dart';
import '../models/healing_prediction.dart';
import '../services/mock_data.dart';
import '../services/api_config.dart';
import '../services/upload_service.dart';

/// Holds the patient's wound photos and the latest healing prediction.
///
/// Runs in one of two modes, decided by [ApiConfig.useRealBackend]:
/// - MOCK (no backend URL set): photos stay in memory, prediction is fake.
/// - REAL (backend URL set): each photo is uploaded to Azure Blob, the cloud
///   pipeline analyses it, and the prediction is read back from
///   get_patient_history.
///
/// Either way the photos also stay in memory so the history/home thumbnails can
/// show the local image immediately (no need to re-download from Blob).
class PhotosProvider extends ChangeNotifier {
  final List<WoundPhoto> _photos = [];
  HealingPrediction? _prediction;
  bool _loading = false;
  String? _status; // e.g. "Analysing…" or an error message

  List<WoundPhoto> get photos => List.unmodifiable(_photos);
  HealingPrediction? get prediction => _prediction;
  bool get isLoading => _loading;
  String? get status => _status;

  /// Photos newest-first (handy for the home "recent" row).
  List<WoundPhoto> get photosNewestFirst {
    final list = [..._photos];
    list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return list;
  }

  /// Day number = days since the patient's first photo. 0 if none yet.
  int nextDayNumber() {
    if (_photos.isEmpty) return 0;
    final first = _photos
        .map((p) => p.timestamp)
        .reduce((a, b) => a.isBefore(b) ? a : b);
    return DateTime.now().difference(first).inDays;
  }

  /// Add a freshly-captured photo. Shows it locally right away, then either
  /// uploads it to the cloud (real backend) or fakes a prediction (mock).
  Future<void> addPhoto(WoundPhoto photo) async {
    _photos.add(photo);
    notifyListeners();

    if (!ApiConfig.useRealBackend) {
      // MOCK mode — unchanged behaviour.
      refreshPrediction(photo.patientId);
      return;
    }

    // REAL mode — upload to Blob, then read the prediction back.
    _loading = true;
    _status = 'Uploading photo…';
    notifyListeners();
    try {
      final imageId = await UploadService.uploadPhoto(
        image: File(photo.localPath),
        patientId: photo.patientId,
        dayNumber: photo.dayNumber,
      );
      // #16 — save the patient-reported pain / symptoms / notes onto the record.
      await UploadService.saveVisitMeta(
        imageId: imageId,
        patientId: photo.patientId,
        painLevel: photo.painLevel,
        symptoms: photo.symptoms,
        notes: photo.notes,
        woundLocation: photo.woundLocation,
      );
      // The blob-trigger function analyses the photo in the background, and the
      // ML endpoint can be slow on its first ("cold") call. So poll the history
      // API for up to ~45s until the result shows up, instead of checking once.
      _status = 'Analysing wound…';
      _loading = true;
      notifyListeners();
      for (int attempt = 0; attempt < 9; attempt++) {
        await Future.delayed(const Duration(seconds: 5));
        final pred = await _fetchRealPrediction(photo.patientId);
        if (pred != null) {
          _prediction = pred;
          _status = null;
          _loading = false;
          notifyListeners();
          return;
        }
      }
      // Gave up waiting — leave a gentle note; the Progress tab can refresh later.
      _status = 'Still analysing — check Progress in a moment';
      _loading = false;
      notifyListeners();
    } catch (e) {
      _status = 'Upload failed: $e';
      _loading = false;
      notifyListeners();
    }
  }

  /// Import several photos at once, each labelled with the real day it was
  /// taken. Uploads them all, then waits for the backend to analyse them and
  /// build the day-by-day trend. Honest onboarding of an existing photo history.
  Future<void> importPhotos(List<WoundPhoto> photos, String patientId) async {
    _photos.addAll(photos);
    notifyListeners();

    if (!ApiConfig.useRealBackend) {
      await refreshPrediction(patientId);
      return;
    }

    _loading = true;
    notifyListeners();
    try {
      for (int i = 0; i < photos.length; i++) {
        _status = 'Uploading ${i + 1}/${photos.length}…';
        notifyListeners();
        await UploadService.uploadPhoto(
          image: File(photos[i].localPath),
          patientId: patientId,
          dayNumber: photos[i].dayNumber,
        );
      }

      // How many distinct days should show up once everything is analysed.
      final wantDays = photos.map((p) => p.dayNumber).toSet().length;
      _status = 'Analysing ${photos.length} photos…';
      notifyListeners();
      for (int attempt = 0; attempt < 15; attempt++) {
        await Future.delayed(const Duration(seconds: 5));
        final pred = await _fetchRealPrediction(patientId);
        if (pred != null) {
          _prediction = pred; // show partial progress as days come in
          notifyListeners();
          if (pred.daySeries.length >= wantDays) {
            _status = null;
            _loading = false;
            notifyListeners();
            return;
          }
        }
      }
      _status = 'Still analysing — check Progress shortly';
      _loading = false;
      notifyListeners();
    } catch (e) {
      _status = 'Import failed: $e';
      _loading = false;
      notifyListeners();
    }
  }

  /// Load the latest prediction — from the cloud if configured, else mock.
  Future<void> refreshPrediction(String patientId) async {
    _loading = true;
    notifyListeners();

    try {
      if (ApiConfig.useRealBackend) {
        _prediction = await _fetchRealPrediction(patientId);
        _status = _prediction == null ? 'No analysis yet' : null;
      } else {
        await Future.delayed(const Duration(milliseconds: 500));
        _prediction = MockData.predictionFor(patientId);
        _status = null;
      }
    } catch (e) {
      _status = 'Could not load prediction: $e';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  /// Call get_patient_history and turn the stored summary into a
  /// [HealingPrediction]. Returns null if there's no analysis yet.
  Future<HealingPrediction?> _fetchRealPrediction(String patientId) async {
    final resp = await http.get(
      ApiConfig.url('get_patient_history', {'patient_id': patientId}),
    );
    if (resp.statusCode != 200) {
      throw Exception('history API ${resp.statusCode}');
    }
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    if (data['status'] == 'no_data') return null;

    // New response shape: { status, prediction, patient }.
    final pred = data['prediction'] as Map<String, dynamic>?;
    if (pred == null) return null; // profile exists but no photo analysed yet

    final tissue = (pred['tissue_series'] as Map?) ?? const {};
    List<double> toD(dynamic l) =>
        (l as List?)?.map((e) => (e as num).toDouble()).toList() ?? const [];
    List<int> toI(dynamic l) =>
        (l as List?)?.map((e) => (e as num).toInt()).toList() ?? const [];

    final enough = pred['enough_visits'] as bool? ?? true;
    final trend = pred['trend'] as String? ?? 'stable';
    return HealingPrediction(
      healingProbability: (pred['healing_probability'] as num?)?.toDouble() ?? 0.0,
      predictedLabel: pred['predicted_label'] as String? ?? 'pending',
      topFactors: ['Overall trend: $trend'],
      daySeries: toI(pred['day_series']),
      areaSeries: toI(pred['area_series']),
      granulation: toD(tissue['granulation']),
      slough: toD(tissue['slough']),
      necrosis: toD(tissue['necrosis']),
      isMock: false, // real data — the "Preview data" badge disappears
      enoughVisits: enough,
      visits: pred['visits'] as int? ?? 0,
    );
  }

  /// Clear everything (called on sign-out).
  void clear() {
    _photos.clear();
    _prediction = null;
    _status = null;
    notifyListeners();
  }
}
