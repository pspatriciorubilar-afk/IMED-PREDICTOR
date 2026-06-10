import 'package:isar/isar.dart';

part 'pvt_session.g.dart';

@collection
class PvtSession {
  Id id = Isar.autoIncrement;

  @Index()
  late DateTime timestamp;

  late double meanLatency;
  late int lapsesCount;
  late int falseStarts;
  
  late List<int> rawReactionTimes;

  @Index()
  bool isSynced = false;

  PvtSession({
    required this.timestamp,
    required this.meanLatency,
    required this.lapsesCount,
    required this.falseStarts,
    required this.rawReactionTimes,
    this.isSynced = false,
  });
}
