// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'pvt_session.dart';

// **************************************************************************
// IsarCollectionGenerator
// **************************************************************************

// coverage:ignore-file
// ignore_for_file: duplicate_ignore, non_constant_identifier_names, constant_identifier_names, invalid_use_of_protected_member, unnecessary_cast, prefer_const_constructors, lines_longer_than_80_chars, require_trailing_commas, inference_failure_on_function_invocation, unnecessary_parenthesis, unnecessary_raw_strings, unnecessary_null_checks, join_return_with_assignment, prefer_final_locals, avoid_js_rounded_ints, avoid_positional_boolean_parameters, always_specify_types

extension GetPvtSessionCollection on Isar {
  IsarCollection<PvtSession> get pvtSessions => this.collection();
}

const PvtSessionSchema = CollectionSchema(
  name: r'PvtSession',
  id: 4835797165328281768,
  properties: {
    r'falseStarts': PropertySchema(
      id: 0,
      name: r'falseStarts',
      type: IsarType.long,
    ),
    r'isSynced': PropertySchema(
      id: 1,
      name: r'isSynced',
      type: IsarType.bool,
    ),
    r'lapsesCount': PropertySchema(
      id: 2,
      name: r'lapsesCount',
      type: IsarType.long,
    ),
    r'meanLatency': PropertySchema(
      id: 3,
      name: r'meanLatency',
      type: IsarType.double,
    ),
    r'rawReactionTimes': PropertySchema(
      id: 4,
      name: r'rawReactionTimes',
      type: IsarType.longList,
    ),
    r'timestamp': PropertySchema(
      id: 5,
      name: r'timestamp',
      type: IsarType.dateTime,
    )
  },
  estimateSize: _pvtSessionEstimateSize,
  serialize: _pvtSessionSerialize,
  deserialize: _pvtSessionDeserialize,
  deserializeProp: _pvtSessionDeserializeProp,
  idName: r'id',
  indexes: {
    r'timestamp': IndexSchema(
      id: 1852253767416892198,
      name: r'timestamp',
      unique: false,
      replace: false,
      properties: [
        IndexPropertySchema(
          name: r'timestamp',
          type: IndexType.value,
          caseSensitive: false,
        )
      ],
    ),
    r'isSynced': IndexSchema(
      id: -39763503327887510,
      name: r'isSynced',
      unique: false,
      replace: false,
      properties: [
        IndexPropertySchema(
          name: r'isSynced',
          type: IndexType.value,
          caseSensitive: false,
        )
      ],
    )
  },
  links: {},
  embeddedSchemas: {},
  getId: _pvtSessionGetId,
  getLinks: _pvtSessionGetLinks,
  attach: _pvtSessionAttach,
  version: '3.1.0+1',
);

int _pvtSessionEstimateSize(
  PvtSession object,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  var bytesCount = offsets.last;
  bytesCount += 3 + object.rawReactionTimes.length * 8;
  return bytesCount;
}

void _pvtSessionSerialize(
  PvtSession object,
  IsarWriter writer,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  writer.writeLong(offsets[0], object.falseStarts);
  writer.writeBool(offsets[1], object.isSynced);
  writer.writeLong(offsets[2], object.lapsesCount);
  writer.writeDouble(offsets[3], object.meanLatency);
  writer.writeLongList(offsets[4], object.rawReactionTimes);
  writer.writeDateTime(offsets[5], object.timestamp);
}

PvtSession _pvtSessionDeserialize(
  Id id,
  IsarReader reader,
  List<int> offsets,
  Map<Type, List<int>> allOffsets,
) {
  final object = PvtSession(
    falseStarts: reader.readLong(offsets[0]),
    isSynced: reader.readBoolOrNull(offsets[1]) ?? false,
    lapsesCount: reader.readLong(offsets[2]),
    meanLatency: reader.readDouble(offsets[3]),
    rawReactionTimes: reader.readLongList(offsets[4]) ?? [],
    timestamp: reader.readDateTime(offsets[5]),
  );
  object.id = id;
  return object;
}

P _pvtSessionDeserializeProp<P>(
  IsarReader reader,
  int propertyId,
  int offset,
  Map<Type, List<int>> allOffsets,
) {
  switch (propertyId) {
    case 0:
      return (reader.readLong(offset)) as P;
    case 1:
      return (reader.readBoolOrNull(offset) ?? false) as P;
    case 2:
      return (reader.readLong(offset)) as P;
    case 3:
      return (reader.readDouble(offset)) as P;
    case 4:
      return (reader.readLongList(offset) ?? []) as P;
    case 5:
      return (reader.readDateTime(offset)) as P;
    default:
      throw IsarError('Unknown property with id $propertyId');
  }
}

Id _pvtSessionGetId(PvtSession object) {
  return object.id;
}

List<IsarLinkBase<dynamic>> _pvtSessionGetLinks(PvtSession object) {
  return [];
}

void _pvtSessionAttach(IsarCollection<dynamic> col, Id id, PvtSession object) {
  object.id = id;
}

extension PvtSessionQueryWhereSort
    on QueryBuilder<PvtSession, PvtSession, QWhere> {
  QueryBuilder<PvtSession, PvtSession, QAfterWhere> anyId() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(const IdWhereClause.any());
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhere> anyTimestamp() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        const IndexWhereClause.any(indexName: r'timestamp'),
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhere> anyIsSynced() {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        const IndexWhereClause.any(indexName: r'isSynced'),
      );
    });
  }
}

extension PvtSessionQueryWhere
    on QueryBuilder<PvtSession, PvtSession, QWhereClause> {
  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> idEqualTo(Id id) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IdWhereClause.between(
        lower: id,
        upper: id,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> idNotEqualTo(Id id) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(
              IdWhereClause.lessThan(upper: id, includeUpper: false),
            )
            .addWhereClause(
              IdWhereClause.greaterThan(lower: id, includeLower: false),
            );
      } else {
        return query
            .addWhereClause(
              IdWhereClause.greaterThan(lower: id, includeLower: false),
            )
            .addWhereClause(
              IdWhereClause.lessThan(upper: id, includeUpper: false),
            );
      }
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> idGreaterThan(Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.greaterThan(lower: id, includeLower: include),
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> idLessThan(Id id,
      {bool include = false}) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(
        IdWhereClause.lessThan(upper: id, includeUpper: include),
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> idBetween(
    Id lowerId,
    Id upperId, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IdWhereClause.between(
        lower: lowerId,
        includeLower: includeLower,
        upper: upperId,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> timestampEqualTo(
      DateTime timestamp) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'timestamp',
        value: [timestamp],
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> timestampNotEqualTo(
      DateTime timestamp) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'timestamp',
              lower: [],
              upper: [timestamp],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'timestamp',
              lower: [timestamp],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'timestamp',
              lower: [timestamp],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'timestamp',
              lower: [],
              upper: [timestamp],
              includeUpper: false,
            ));
      }
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> timestampGreaterThan(
    DateTime timestamp, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.between(
        indexName: r'timestamp',
        lower: [timestamp],
        includeLower: include,
        upper: [],
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> timestampLessThan(
    DateTime timestamp, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.between(
        indexName: r'timestamp',
        lower: [],
        upper: [timestamp],
        includeUpper: include,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> timestampBetween(
    DateTime lowerTimestamp,
    DateTime upperTimestamp, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.between(
        indexName: r'timestamp',
        lower: [lowerTimestamp],
        includeLower: includeLower,
        upper: [upperTimestamp],
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> isSyncedEqualTo(
      bool isSynced) {
    return QueryBuilder.apply(this, (query) {
      return query.addWhereClause(IndexWhereClause.equalTo(
        indexName: r'isSynced',
        value: [isSynced],
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterWhereClause> isSyncedNotEqualTo(
      bool isSynced) {
    return QueryBuilder.apply(this, (query) {
      if (query.whereSort == Sort.asc) {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'isSynced',
              lower: [],
              upper: [isSynced],
              includeUpper: false,
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'isSynced',
              lower: [isSynced],
              includeLower: false,
              upper: [],
            ));
      } else {
        return query
            .addWhereClause(IndexWhereClause.between(
              indexName: r'isSynced',
              lower: [isSynced],
              includeLower: false,
              upper: [],
            ))
            .addWhereClause(IndexWhereClause.between(
              indexName: r'isSynced',
              lower: [],
              upper: [isSynced],
              includeUpper: false,
            ));
      }
    });
  }
}

extension PvtSessionQueryFilter
    on QueryBuilder<PvtSession, PvtSession, QFilterCondition> {
  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      falseStartsEqualTo(int value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'falseStarts',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      falseStartsGreaterThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'falseStarts',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      falseStartsLessThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'falseStarts',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      falseStartsBetween(
    int lower,
    int upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'falseStarts',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> idEqualTo(
      Id value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> idGreaterThan(
    Id value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> idLessThan(
    Id value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'id',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> idBetween(
    Id lower,
    Id upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'id',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> isSyncedEqualTo(
      bool value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'isSynced',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      lapsesCountEqualTo(int value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'lapsesCount',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      lapsesCountGreaterThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'lapsesCount',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      lapsesCountLessThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'lapsesCount',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      lapsesCountBetween(
    int lower,
    int upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'lapsesCount',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      meanLatencyEqualTo(
    double value, {
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'meanLatency',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      meanLatencyGreaterThan(
    double value, {
    bool include = false,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'meanLatency',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      meanLatencyLessThan(
    double value, {
    bool include = false,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'meanLatency',
        value: value,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      meanLatencyBetween(
    double lower,
    double upper, {
    bool includeLower = true,
    bool includeUpper = true,
    double epsilon = Query.epsilon,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'meanLatency',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
        epsilon: epsilon,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesElementEqualTo(int value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'rawReactionTimes',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesElementGreaterThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'rawReactionTimes',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesElementLessThan(
    int value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'rawReactionTimes',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesElementBetween(
    int lower,
    int upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'rawReactionTimes',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesLengthEqualTo(int length) {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        length,
        true,
        length,
        true,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesIsEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        0,
        true,
        0,
        true,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesIsNotEmpty() {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        0,
        false,
        999999,
        true,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesLengthLessThan(
    int length, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        0,
        true,
        length,
        include,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesLengthGreaterThan(
    int length, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        length,
        include,
        999999,
        true,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      rawReactionTimesLengthBetween(
    int lower,
    int upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.listLength(
        r'rawReactionTimes',
        lower,
        includeLower,
        upper,
        includeUpper,
      );
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> timestampEqualTo(
      DateTime value) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.equalTo(
        property: r'timestamp',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition>
      timestampGreaterThan(
    DateTime value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.greaterThan(
        include: include,
        property: r'timestamp',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> timestampLessThan(
    DateTime value, {
    bool include = false,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.lessThan(
        include: include,
        property: r'timestamp',
        value: value,
      ));
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterFilterCondition> timestampBetween(
    DateTime lower,
    DateTime upper, {
    bool includeLower = true,
    bool includeUpper = true,
  }) {
    return QueryBuilder.apply(this, (query) {
      return query.addFilterCondition(FilterCondition.between(
        property: r'timestamp',
        lower: lower,
        includeLower: includeLower,
        upper: upper,
        includeUpper: includeUpper,
      ));
    });
  }
}

extension PvtSessionQueryObject
    on QueryBuilder<PvtSession, PvtSession, QFilterCondition> {}

extension PvtSessionQueryLinks
    on QueryBuilder<PvtSession, PvtSession, QFilterCondition> {}

extension PvtSessionQuerySortBy
    on QueryBuilder<PvtSession, PvtSession, QSortBy> {
  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByFalseStarts() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'falseStarts', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByFalseStartsDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'falseStarts', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByIsSynced() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'isSynced', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByIsSyncedDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'isSynced', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByLapsesCount() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'lapsesCount', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByLapsesCountDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'lapsesCount', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByMeanLatency() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'meanLatency', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByMeanLatencyDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'meanLatency', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByTimestamp() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'timestamp', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> sortByTimestampDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'timestamp', Sort.desc);
    });
  }
}

extension PvtSessionQuerySortThenBy
    on QueryBuilder<PvtSession, PvtSession, QSortThenBy> {
  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByFalseStarts() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'falseStarts', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByFalseStartsDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'falseStarts', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenById() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByIdDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'id', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByIsSynced() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'isSynced', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByIsSyncedDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'isSynced', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByLapsesCount() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'lapsesCount', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByLapsesCountDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'lapsesCount', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByMeanLatency() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'meanLatency', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByMeanLatencyDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'meanLatency', Sort.desc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByTimestamp() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'timestamp', Sort.asc);
    });
  }

  QueryBuilder<PvtSession, PvtSession, QAfterSortBy> thenByTimestampDesc() {
    return QueryBuilder.apply(this, (query) {
      return query.addSortBy(r'timestamp', Sort.desc);
    });
  }
}

extension PvtSessionQueryWhereDistinct
    on QueryBuilder<PvtSession, PvtSession, QDistinct> {
  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByFalseStarts() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'falseStarts');
    });
  }

  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByIsSynced() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'isSynced');
    });
  }

  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByLapsesCount() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'lapsesCount');
    });
  }

  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByMeanLatency() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'meanLatency');
    });
  }

  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByRawReactionTimes() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'rawReactionTimes');
    });
  }

  QueryBuilder<PvtSession, PvtSession, QDistinct> distinctByTimestamp() {
    return QueryBuilder.apply(this, (query) {
      return query.addDistinctBy(r'timestamp');
    });
  }
}

extension PvtSessionQueryProperty
    on QueryBuilder<PvtSession, PvtSession, QQueryProperty> {
  QueryBuilder<PvtSession, int, QQueryOperations> idProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'id');
    });
  }

  QueryBuilder<PvtSession, int, QQueryOperations> falseStartsProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'falseStarts');
    });
  }

  QueryBuilder<PvtSession, bool, QQueryOperations> isSyncedProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'isSynced');
    });
  }

  QueryBuilder<PvtSession, int, QQueryOperations> lapsesCountProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'lapsesCount');
    });
  }

  QueryBuilder<PvtSession, double, QQueryOperations> meanLatencyProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'meanLatency');
    });
  }

  QueryBuilder<PvtSession, List<int>, QQueryOperations>
      rawReactionTimesProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'rawReactionTimes');
    });
  }

  QueryBuilder<PvtSession, DateTime, QQueryOperations> timestampProperty() {
    return QueryBuilder.apply(this, (query) {
      return query.addPropertyName(r'timestamp');
    });
  }
}
