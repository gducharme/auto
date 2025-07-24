from auto.cli import maintenance
from auto.db import SessionLocal
from auto.models import Post


def test_dump_and_load_fixtures(test_db_engine, tmp_path):
    dump_file = tmp_path / "dump.sql"

    with SessionLocal() as session:
        session.add(Post(id="1", title="T", link="http://ex"))
        session.commit()

    maintenance.dump_fixtures(path=str(dump_file))

    maintenance.load_fixtures(path=str(dump_file))

    with SessionLocal() as session:
        posts = session.query(Post).all()
        assert len(posts) == 1
        assert posts[0].id == "1"
