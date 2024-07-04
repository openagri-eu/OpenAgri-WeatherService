db.getSiblingDB('openagridb');
db.createUser({
    user: 'openagri',
    pwd: 'openagri',
    roles: [
        {
            role: 'readWrite',
            db: 'openagridb',
        },
    ],
});
db.points.createIndex(
    { "location": "2dsphere" }
  );