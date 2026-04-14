import 'package:flutter/material.dart';

void main() {
  runApp(ScreenTimeApp());
}

class ScreenTimeApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Screen Time Tracker',
      theme: ThemeData.dark(),
      home: HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Screen Time Tracker'),
      ),
      body: Center(
        child: Text(
          'Welcome 👋',
          style: TextStyle(fontSize: 24),
        ),
      ),
    );
  }
}
