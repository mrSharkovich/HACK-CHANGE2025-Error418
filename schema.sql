CREATE TABLE IF NOT EXISTS "comments" (
  "id"  INTEGER NOT NULL,
  "comment"  TEXT NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "courses" (
  "id"  INTEGER NOT NULL,
  "title"  VARCHAR(100) NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "homework_answers" (
  "id"  INTEGER NOT NULL,
  "lesson_id"  INTEGER NOT NULL,
  "user_id"  INTEGER NOT NULL,
  "answer_text"  TEXT,
  "file_path"  VARCHAR(255),
  "file_name"  VARCHAR(255),
  "submitted_at"  DATETIME DEFAULT CURRENT_TIMESTAMP,
  "status"  VARCHAR(20) DEFAULT 'pending',
  "comment_id"  INTEGER,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "lesson_materials" (
  "id"  INTEGER,
  "lesson_id"  INTEGER NOT NULL,
  "type"  TEXT NOT NULL,
  "title"  TEXT NOT NULL,
  "youtube_id"  TEXT,
  "file_path"  TEXT,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "lessons" (
  "id"  INTEGER NOT NULL,
  "title"  TEXT NOT NULL,
  "content"  TEXT NOT NULL,
  "home_work"  INTEGER NOT NULL,
  "order_index"  INTEGER NOT NULL,
  "course_id"  INTEGER NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "user_courses" (
  "id"  INTEGER NOT NULL,
  "user_id"  INTEGER NOT NULL,
  "course_id"  INTEGER NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "users" (
  "id"  INTEGER NOT NULL,
  "login"  VARCHAR(25) NOT NULL UNIQUE,
  "password"  VARCHAR(25) NOT NULL,
  "last_name"  VARCHAR(50) NOT NULL,
  "first_name"  VARCHAR(50) NOT NULL,
  PRIMARY KEY("id" AUTOINCREMENT)
);

CREATE TABLE IF NOT EXISTS "user_progress" (
  "user_id" INTEGER NOT NULL,
  "lesson_id" INTEGER NOT NULL,
  "completed" BOOLEAN NOT NULL DEFAULT 0,
  PRIMARY KEY("user_id", "lesson_id")
);