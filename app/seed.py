from app.database import db_session
from app.models import Trainer, FitnessCenter


def seed_data():
    # Create Fitness Center if missing
    fc = db_session.query(FitnessCenter).first()
    if not fc:
        fc = FitnessCenter(
            name="PowerHouse Gym",
            address="123 Fitness St, NY",
            contacts="+1 555 123 456"
        )
        db_session.add(fc)
        db_session.commit()

    # Create Trainers
    trainers = [
        Trainer(name="John Carter", gym_id=fc.id),
        Trainer(name="Emily Stone", gym_id=fc.id),
        Trainer(name="Michael Johnson", gym_id=fc.id)
    ]

    for t in trainers:
        db_session.add(t)

    db_session.commit()
    print("Trainers & Fitness Center added successfully!")
