from werkzeug.security import generate_password_hash
def create_initial_data(db, Entity, User):
    """Create initial data if it doesn't already exist."""
    # Create Group Entity
    group_entity = Entity.query.filter_by(name="Group").first()
    if not group_entity:
        group_entity = Entity(name="Group", entity_type="Company")
        db.session.add(group_entity)
        db.session.flush()

    # Create Subsidiaries
    subsidiary1 = Entity.query.filter_by(name="Subsidiary 1").first()
    if not subsidiary1:
        subsidiary1 = Entity(name="Subsidiary 1", entity_type="Company", parent_id=group_entity.id)
        db.session.add(subsidiary1)
        db.session.flush()

    subsidiary2 = Entity.query.filter_by(name="Subsidiary 2").first()
    if not subsidiary2:
        subsidiary2 = Entity(name="Subsidiary 2", entity_type="Company", parent_id=subsidiary1.id)
        db.session.add(subsidiary2)
        db.session.flush()

    # Create Teams
    internal_team1 = Entity.query.filter_by(name="Internal Team 1").first()
    if not internal_team1:
        internal_team1 = Entity(name="Internal Team 1", entity_type="Team", parent_id=subsidiary1.id)
        db.session.add(internal_team1)
        db.session.flush()

    internal_team2 = Entity.query.filter_by(name="Internal Team 2").first()
    if not internal_team2:
        internal_team2 = Entity(name="Internal Team 2", entity_type="Team", parent_id=subsidiary2.id)
        db.session.add(internal_team2)
        db.session.flush()

    # Create Users
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="prateek.deoli@gmail.com",
            password="adminpass",
            role="Admin",
            entity_id=group_entity.id
        )
        db.session.add(admin_user)

    user1 = User.query.filter_by(username="user1").first()
    if not user1:
        user1 = User(
            username="user1",
            email="user1@yopmail.com",
            password='user1pass',
            role="User",
            entity_id=subsidiary1.id
        )
        db.session.add(user1)

    user1_2 = User.query.filter_by(username="user1_2").first()
    if not user1_2:
        user1_2 = User(
            username="user1_2",
            email="user1_2@yopmail.com",
            password='user1_2pass',
            role="User",
            entity_id=internal_team1.id
        )
        db.session.add(user1_2)

    user2 = User.query.filter_by(username="user2").first()
    if not user2:
        user2 = User(
            username="user2",
            email="user2@yopmail.com",
            password="user2pass",
            role="User",
            entity_id=subsidiary2.id
        )
        db.session.add(user2)

    # Commit changes
    db.session.commit()
