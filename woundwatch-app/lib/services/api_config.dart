/// Central place for the backend URLs.
///
/// SECURITY: do NOT commit real URLs/keys here — this repo is public. Fill these
/// in only in your LOCAL copy. Empty values keep the app in safe "mock mode".
///
/// HOW THE FLIP WORKS:
/// - While [functionBaseUrl] is empty, the app runs in mock mode (fake data).
/// - Set it to your deployed Function App base URL
///   (e.g. https://<your-app>.azurewebsites.net/api) locally to use the real
///   backend. The `?code=...` function key goes in [functionKey].
class ApiConfig {
  ApiConfig._();

  /// Base URL of the deployed Function App. Empty = mock mode.
  /// Set this locally; keep it empty in the committed file.
  static const String functionBaseUrl = "";

  /// Function key appended as ?code=... Set locally; keep empty in git.
  static const String functionKey = "";

  /// True when a real backend URL has been configured.
  static bool get useRealBackend => functionBaseUrl.isNotEmpty;

  /// Build a full function URL with query params (adds the key if present).
  static Uri url(String path, Map<String, String> params) {
    final qp = {...params, if (functionKey.isNotEmpty) 'code': functionKey};
    return Uri.parse('$functionBaseUrl/$path').replace(queryParameters: qp);
  }
}
