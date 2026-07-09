import 'package:flutter/foundation.dart';
import '../models/wound_photo.dart';
import '../models/healing_prediction.dart';
import '../services/mock_data.dart';

/// Holds the patient's wound photos and the latest healing prediction.
///
/// PHASE 1 (now): photos are kept in memory and the prediction is mock.
/// PHASE 2/3 (later): fetchPhotos() reads Firestore, addPhoto() uploads to
/// Azure, and refreshPrediction() calls the real pipeline API.
class PhotosProvider extends ChangeNotifier {
  final List<WoundPhoto> _photos = [];
  HealingPrediction? _prediction;
  bool _loading = false;

  List<WoundPhoto> get photos => List.unmodifiable(_photos);
  HealingPrediction? get prediction => _prediction;
  bool get isLoading => _loading;

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

  void addPhoto(WoundPhoto photo) {
    _photos.add(photo);
    notifyListeners();
    // A new photo means the prediction should update.
    refreshPrediction(photo.patientId);
  }

  /// Recompute the healing prediction. Mock for now.
  Future<void> refreshPrediction(String patientId) async {
    _loading = true;
    notifyListeners();
    await Future.delayed(const Duration(milliseconds: 500)); // fake network
    _prediction = MockData.predictionFor(patientId);
    _loading = false;
    notifyListeners();
  }

  /// Clear everything (called on sign-out).
  void clear() {
    _photos.clear();
    _prediction = null;
    notifyListeners();
  }
}
