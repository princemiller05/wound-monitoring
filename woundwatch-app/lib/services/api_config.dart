/// Central place for the backend URLs.
///
/// HOW THE FLIP WORKS:
/// - While [functionBaseUrl] is empty, the app runs in **mock mode** — photos
///   stay in memory and predictions are fake (the way it works today).
/// - Once you deploy the Azure Functions, paste the Function App base URL here
///   (e.g. https://woundwatch-api.azurewebsites.net/api) and the app switches to
///   the **real backend**: photos upload to Blob, and predictions come from the
///   pipeline via get_patient_history.
///
/// The `?code=...` function key (if your functions use authLevel "function")
/// goes in [functionKey]. Never commit real keys to a public repo — for a quick
/// demo it's okay locally, but for production pass it more securely.
class ApiConfig {
  ApiConfig._();

  /// Base URL of the deployed Function App, e.g.
  /// "https://woundwatch-api.azurewebsites.net/api". Empty = mock mode.
  static const String functionBaseUrl =
      "https://woundwatch-api-2026.azurewebsites.net/api";

  /// Function key appended as ?code=... (leave empty if not needed).
  static const String functionKey = "";

  /// True when a real backend URL has been configured.
  static bool get useRealBackend => functionBaseUrl.isNotEmpty;

  /// Build a full function URL with query params (adds the key if present).
  static Uri url(String path, Map<String, String> params) {
    final qp = {...params, if (functionKey.isNotEmpty) 'code': functionKey};
    return Uri.parse('$functionBaseUrl/$path').replace(queryParameters: qp);
  }
}
