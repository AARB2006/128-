
from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Playlist(Base):
    __tablename__ = "playlists"

    playlist_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    playlist_songs = relationship(
        "PlaylistSong",
        back_populates="playlist",
        cascade="all, delete-orphan"
    )


class Song(Base):
    __tablename__ = "songs"

    song_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(
        String(20, collation="ascii_bin"),
        nullable=False,
        unique=True
    )
    source_url = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    date_added = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    playlist_songs = relationship(
        "PlaylistSong",
        back_populates="song"
    )


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    playlist_song_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    playlist_id = Column(
        Integer,
        ForeignKey("playlists.playlist_id", ondelete="CASCADE"),
        nullable=False
    )

    song_id = Column(
        Integer,
        ForeignKey("songs.song_id", ondelete="RESTRICT"),
        nullable=False
    )

    position = Column(Integer, nullable=False)
    added_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        UniqueConstraint(
            "playlist_id",
            "song_id",
            name="uq_playlist_song"
        ),
        UniqueConstraint(
            "playlist_id",
            "position",
            name="uq_playlist_position"
        ),
        CheckConstraint(
            "position > 0",
            name="chk_position"
        )
    )

    playlist = relationship(
        "Playlist",
        back_populates="playlist_songs"
    )

    song = relationship(
        "Song",
        back_populates="playlist_songs"
    )
