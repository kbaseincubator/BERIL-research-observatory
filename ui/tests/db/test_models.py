"""Tests for SQLAlchemy ORM models (app.db.models)."""

import pytest

from app.db.models import (
    BerilUser,
    ProjectCollection,
    ProjectContributor,
    ProjectFile,
    ProjectReview,
    UserApiToken,
    UserProject,
)


# ---------------------------------------------------------------------------
# BerilUser
# ---------------------------------------------------------------------------


class TestBerilUser:
    async def test_create_minimal(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert len(user.id) == 36  # UUID string
        assert user.orcid_id == "0000-0001-2345-6789"
        assert user.display_name is None
        assert user.affiliation is None
        assert user.is_active is True
        assert user.created_at is not None
        assert user.last_login_at is not None

    async def test_create_with_all_fields(self, db_session):
        user = BerilUser(
            orcid_id="0000-0002-3456-7890",
            display_name="Alice Researcher",
            affiliation="Lawrence Berkeley National Laboratory",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.display_name == "Alice Researcher"
        assert user.affiliation == "Lawrence Berkeley National Laboratory"

    async def test_orcid_id_is_unique(self, db_session):
        from sqlalchemy.exc import IntegrityError

        user1 = BerilUser(orcid_id="0000-0001-1111-1111")
        user2 = BerilUser(orcid_id="0000-0001-1111-1111")
        db_session.add(user1)
        await db_session.commit()

        db_session.add(user2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_two_users_have_distinct_uuids(self, db_session):
        user1 = BerilUser(orcid_id="0000-0001-0001-0001")
        user2 = BerilUser(orcid_id="0000-0001-0002-0002")
        db_session.add_all([user1, user2])
        await db_session.commit()
        await db_session.refresh(user1)
        await db_session.refresh(user2)

        assert user1.id != user2.id

    async def test_inactive_user(self, db_session):
        user = BerilUser(orcid_id="0000-0001-9999-9999", is_active=False)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.is_active is False


# ---------------------------------------------------------------------------
# UserProject
# ---------------------------------------------------------------------------


class TestUserProject:
    @pytest.fixture
    async def user(self, db_session):
        u = BerilUser(orcid_id="0000-0001-2345-6789", display_name="Alice")
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        return u

    async def test_create_minimal(self, db_session, user):
        project = UserProject(
            owner_id=user.id,
            slug="my-first-project",
            title="My First Project",
            research_question="Does X cause Y?",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.id is not None
        assert project.owner_id == user.id
        assert project.slug == "my-first-project"
        assert project.status == "proposed"
        assert project.is_public is False
        assert project.submitted_at is None
        assert project.hypothesis is None

    async def test_filesystem_path_parts(self, db_session, user):
        project = UserProject(
            owner_id=user.id,
            slug="my-project",
            title="T",
            research_question="Q?",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        owner_id, slug = project.filesystem_path_parts
        assert owner_id == user.id
        assert slug == "my-project"

    async def test_status_values(self, db_session, user):
        for status in ("proposed", "in_progress", "completed"):
            project = UserProject(
                owner_id=user.id,
                slug=f"project-{status}",
                title="T",
                research_question="Q?",
                status=status,
            )
            db_session.add(project)
        await db_session.commit()

    async def test_github_repo_url_defaults_none(self, db_session, user):
        project = UserProject(
            owner_id=user.id,
            slug="no-github",
            title="T",
            research_question="Q?",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.github_repo_url is None

    async def test_github_repo_url_can_be_set(self, db_session, user):
        project = UserProject(
            owner_id=user.id,
            slug="with-github",
            title="T",
            research_question="Q?",
            github_repo_url="https://github.com/org/repo",
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        assert project.github_repo_url == "https://github.com/org/repo"

    async def test_cascade_delete_removes_project(self, db_session, user):
        from sqlalchemy import select

        project = UserProject(
            owner_id=user.id,
            slug="doomed",
            title="T",
            research_question="Q?",
        )
        db_session.add(project)
        await db_session.commit()
        project_id = project.id

        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(
            select(UserProject).where(UserProject.id == project_id)
        )
        assert result.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# ProjectContributor
# ---------------------------------------------------------------------------


class TestProjectContributor:
    @pytest.fixture
    async def user_and_project(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = UserProject(
            owner_id=user.id, slug="p", title="T", research_question="Q?"
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return user, project

    async def test_create_registered_contributor(self, db_session, user_and_project):
        user, project = user_and_project
        contrib = ProjectContributor(
            project_id=project.id,
            user_id=user.id,
            name="Alice",
            orcid_id="0000-0001-2345-6789",
            role="Author",
        )
        db_session.add(contrib)
        await db_session.commit()
        await db_session.refresh(contrib)

        assert contrib.id is not None
        assert contrib.user_id == user.id
        assert contrib.role == "Author"

    async def test_create_unregistered_contributor(self, db_session, user_and_project):
        _, project = user_and_project
        contrib = ProjectContributor(
            project_id=project.id,
            user_id=None,
            name="External Bob",
            orcid_id="0000-0002-9999-8888",
        )
        db_session.add(contrib)
        await db_session.commit()
        await db_session.refresh(contrib)

        assert contrib.user_id is None
        assert contrib.name == "External Bob"

    async def test_default_role_is_author(self, db_session, user_and_project):
        _, project = user_and_project
        contrib = ProjectContributor(project_id=project.id, name="Someone")
        db_session.add(contrib)
        await db_session.commit()
        await db_session.refresh(contrib)

        assert contrib.role == "Author"


# ---------------------------------------------------------------------------
# ProjectFile
# ---------------------------------------------------------------------------


class TestProjectFile:
    @pytest.fixture
    async def project(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        p = UserProject(owner_id=user.id, slug="p", title="T", research_question="Q?")
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        return p

    async def test_create_notebook_file(self, db_session, project):
        f = ProjectFile(
            project_id=project.id,
            file_type="notebook",
            filename="analysis.ipynb",
            storage_path=f"{project.id}/notebooks/analysis.ipynb",
            size_bytes=42_000,
            content_type="application/x-ipynb+json",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        assert f.id is not None
        assert f.file_type == "notebook"
        assert f.size_bytes == 42_000
        assert f.title is None
        assert f.uploaded_at is not None

    async def test_all_file_types_accepted(self, db_session, project):
        for ftype in ("notebook", "data", "visualization", "readme", "research_plan", "report", "other"):
            f = ProjectFile(
                project_id=project.id,
                file_type=ftype,
                filename=f"file.{ftype}",
                storage_path=f"{project.id}/{ftype}/file",
            )
            db_session.add(f)
        await db_session.commit()

    async def test_is_public_defaults_false(self, db_session, project):
        f = ProjectFile(
            project_id=project.id,
            file_type="data",
            filename="data.csv",
            storage_path=f"{project.id}/data/data.csv",
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        assert f.is_public is False

    async def test_is_public_can_be_set_true(self, db_session, project):
        f = ProjectFile(
            project_id=project.id,
            file_type="data",
            filename="public.csv",
            storage_path=f"{project.id}/data/public.csv",
            is_public=True,
        )
        db_session.add(f)
        await db_session.commit()
        await db_session.refresh(f)

        assert f.is_public is True


# ---------------------------------------------------------------------------
# ProjectReview
# ---------------------------------------------------------------------------


class TestProjectReview:
    @pytest.fixture
    async def project(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        p = UserProject(owner_id=user.id, slug="p", title="T", research_question="Q?")
        db_session.add(p)
        await db_session.commit()
        await db_session.refresh(p)
        return p

    async def test_create_review(self, db_session, project):
        review = ProjectReview(
            project_id=project.id,
            reviewer="claude-opus-4",
            summary="Solid methodology.",
            raw_content="# Review\n\nSolid methodology.",
        )
        db_session.add(review)
        await db_session.commit()
        await db_session.refresh(review)

        assert review.id is not None
        assert review.reviewer == "claude-opus-4"
        assert review.reviewed_at is not None
        assert review.methodology is None

    async def test_multiple_reviews_append(self, db_session, project):
        from sqlalchemy import select

        for i in range(3):
            db_session.add(ProjectReview(
                project_id=project.id,
                reviewer=f"reviewer-{i}",
                raw_content=f"Review {i}",
            ))
        await db_session.commit()

        result = await db_session.execute(
            select(ProjectReview).where(ProjectReview.project_id == project.id)
        )
        reviews = result.scalars().all()
        assert len(reviews) == 3


# ---------------------------------------------------------------------------
# ProjectCollection
# ---------------------------------------------------------------------------


class TestProjectCollection:
    async def test_create_collection_link(self, db_session):
        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = UserProject(
            owner_id=user.id, slug="p", title="T", research_question="Q?"
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        link = ProjectCollection(
            project_id=project.id, collection_id="kbase_ke_pangenome"
        )
        db_session.add(link)
        await db_session.commit()

        assert link.project_id == project.id
        assert link.collection_id == "kbase_ke_pangenome"

    async def test_composite_pk_prevents_duplicates(self, db_session):
        from sqlalchemy.exc import IntegrityError

        user = BerilUser(orcid_id="0000-0001-2345-6789")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        project = UserProject(
            owner_id=user.id, slug="p", title="T", research_question="Q?"
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        link1 = ProjectCollection(project_id=project.id, collection_id="coll_a")
        link2 = ProjectCollection(project_id=project.id, collection_id="coll_a")
        db_session.add(link1)
        await db_session.commit()

        db_session.add(link2)
        with pytest.raises(IntegrityError):
            await db_session.commit()


# ---------------------------------------------------------------------------
# UserApiToken
# ---------------------------------------------------------------------------


class TestUserApiToken:
    @pytest.fixture
    async def user(self, db_session):
        u = BerilUser(orcid_id="0000-0001-2345-6789", display_name="Alice")
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        return u

    async def test_create_token(self, db_session, user):
        token = UserApiToken(
            user_id=user.id,
            token_hash="abc123deadbeef" * 4,
        )
        db_session.add(token)
        await db_session.commit()
        await db_session.refresh(token)

        assert token.id is not None
        assert len(token.id) == 36
        assert token.user_id == user.id
        assert token.token_hash == "abc123deadbeef" * 4
        assert token.created_at is not None
        assert token.last_used_at is None

    async def test_token_hash_is_unique(self, db_session, user):
        from sqlalchemy.exc import IntegrityError

        hash_val = "deadbeef" * 8
        t1 = UserApiToken(user_id=user.id, token_hash=hash_val)
        t2 = UserApiToken(user_id=user.id, token_hash=hash_val)
        db_session.add(t1)
        await db_session.commit()

        db_session.add(t2)
        with pytest.raises(IntegrityError):
            await db_session.commit()

    async def test_cascade_delete_removes_token(self, db_session, user):
        from sqlalchemy import select

        token = UserApiToken(user_id=user.id, token_hash="cafebabe" * 8)
        db_session.add(token)
        await db_session.commit()
        token_id = token.id

        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(
            select(UserApiToken).where(UserApiToken.id == token_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_user_can_have_multiple_tokens(self, db_session, user):
        from sqlalchemy import select

        for i in range(3):
            db_session.add(UserApiToken(user_id=user.id, token_hash=f"hash{i}" * 10))
        await db_session.commit()

        result = await db_session.execute(
            select(UserApiToken).where(UserApiToken.user_id == user.id)
        )
        assert len(result.scalars().all()) == 3
