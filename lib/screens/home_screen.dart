import 'package:flutter/material.dart';

class TrackingScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Screen Time Tracking'),
      ),
      body: Column(
        children: <Widget>[
          TimeCard(period: 'Daily'),
          TimeCard(period: 'Weekly'),
          TimeCard(period: 'Monthly'),
          ElevatedButton(
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => SettingsScreen()),
              );
            },
            child: Text('Settings'),
          ),
        ],
      ),
    );
  }
}

class SettingsScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Settings'),
      ),
      body: Center(
        child: Text('Settings Page'),
      ),
    );
  }
}

class TimeCard extends StatelessWidget {
  final String period;

  TimeCard({required this.period});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16.0),
        child: Text('Screen time for $period'),
      ),
    );
  }
}
