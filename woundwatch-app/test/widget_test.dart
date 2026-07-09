// Basic smoke test: the app builds and shows the login screen.
import 'package:flutter_test/flutter_test.dart';
import 'package:woundwatch/main.dart';

void main() {
  testWidgets('App launches to the login screen', (tester) async {
    await tester.pumpWidget(const WoundWatchApp());
    await tester.pumpAndSettle();

    expect(find.text('WoundWatch'), findsOneWidget);
    expect(find.text('Log In'), findsOneWidget);
  });
}
