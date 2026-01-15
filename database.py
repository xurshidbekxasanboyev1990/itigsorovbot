# database.py - SQLite ma'lumotlar bazasi

import sqlite3
import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, List, Any
from contextlib import asynccontextmanager
import threading


class Database:
    """Thread-safe SQLite database manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._init_lock = asyncio.Lock()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def _get_connection(self):
        """Har bir thread uchun alohida connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
                isolation_level=None
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA cache_size=10000")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
        return self._local.connection
    
    @asynccontextmanager
    async def get_cursor(self):
        """Async cursor"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    async def get_next_unique_id(self) -> str:
        """Keyingi unikal ID (1, 2, 3, ...)"""
        async with self.get_cursor() as cursor:
            cursor.execute("SELECT MAX(CAST(unique_id AS INTEGER)) as max_id FROM students WHERE unique_id IS NOT NULL")
            row = cursor.fetchone()
            if row and row['max_id']:
                next_id = int(row['max_id']) + 1
            else:
                next_id = 1
            return str(next_id)
    
    async def init_db(self):
        """Ma'lumotlar bazasini yaratish"""
        async with self._init_lock:
            async with self.get_cursor() as cursor:
                # Talabalar jadvali - Excel ustunlari bilan
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unique_id TEXT UNIQUE NOT NULL,
                        talaba_id TEXT,
                        fullname TEXT NOT NULL,
                        citizenship TEXT,
                        country TEXT,
                        nationality TEXT,
                        region TEXT,
                        district TEXT,
                        gender TEXT,
                        birth_date TEXT,
                        passport TEXT,
                        jshshir TEXT,
                        passport_date TEXT,
                        course TEXT,
                        faculty TEXT,
                        group_name TEXT,
                        language TEXT,
                        study_year TEXT,
                        semester TEXT,
                        graduate TEXT,
                        specialty TEXT,
                        education_type TEXT,
                        education_form TEXT,
                        payment_type TEXT,
                        grant_type TEXT,
                        previous_education TEXT,
                        student_category TEXT,
                        social_category TEXT,
                        family_members TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # So'rovnoma javoblari jadvali
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS survey_responses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        unique_id TEXT NOT NULL,
                        fullname TEXT,
                        group_name TEXT,
                        
                        -- Asosiy ma'lumotlar
                        phone TEXT,
                        permanent_address TEXT,
                        permanent_location TEXT,
                        previous_education TEXT,
                        document_number TEXT,
                        
                        -- Yutuqlar
                        has_achievements TEXT,
                        achievements TEXT,
                        
                        -- Sertifikat
                        has_certificate TEXT,
                        certificate_type TEXT,
                        certificate_details TEXT,
                        certificate_file TEXT,
                        
                        -- Grant
                        has_grant TEXT,
                        grant_details TEXT,
                        
                        -- Ijtimoiy holat
                        social_protection TEXT,
                        iron_book TEXT,
                        youth_book TEXT,
                        
                        -- Ota ma'lumotlari
                        father_name TEXT,
                        father_alive TEXT,
                        father_phone TEXT,
                        
                        -- Ona ma'lumotlari
                        mother_name TEXT,
                        mother_alive TEXT,
                        mother_phone TEXT,
                        parents_together TEXT,
                        
                        -- Yashash joyi
                        living_type TEXT,
                        ttj_location TEXT,
                        rent_address TEXT,
                        rent_location TEXT,
                        rent_owner TEXT,
                        
                        -- Ish
                        is_working TEXT,
                        workplace TEXT,
                        
                        -- Oila holati
                        is_married TEXT,
                        
                        -- Pasport va ijtimoiy tarmoqlar
                        has_foreign_passport TEXT,
                        has_social_channels TEXT,
                        social_links TEXT,
                        
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (unique_id) REFERENCES students(unique_id)
                    )
                """)
                
                # Xodimlar jadvali
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS staff (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE NOT NULL,
                        fullname TEXT,
                        added_by INTEGER,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Foydalanuvchilar holati
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_states (
                        user_id INTEGER PRIMARY KEY,
                        current_state TEXT,
                        temp_data TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexlar
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_unique_id ON students(unique_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_passport ON students(passport)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_jshshir ON students(jshshir)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_talaba_id ON students(talaba_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_survey_unique_id ON survey_responses(unique_id)")
    
    async def find_student(self, search_value: str) -> Optional[Dict[str, Any]]:
        """Talabani qidirish (unique_id, passport, talaba_id, jshshir)"""
        search_value = search_value.strip().upper()
        
        async with self.get_cursor() as cursor:
            # JSHSHIR (14 raqam)
            if search_value.isdigit() and len(search_value) == 14:
                cursor.execute("SELECT * FROM students WHERE jshshir = ?", (search_value,))
            # Talaba ID (12 raqam)
            elif search_value.isdigit() and len(search_value) == 12:
                cursor.execute("SELECT * FROM students WHERE talaba_id = ?", (search_value,))
            # Boshqa raqamlar (unique_id yoki talaba_id)
            elif search_value.isdigit():
                cursor.execute("SELECT * FROM students WHERE unique_id = ? OR talaba_id = ?", (search_value, search_value))
            # Passport (AA1234567)
            else:
                cursor.execute("SELECT * FROM students WHERE UPPER(passport) = ?", (search_value,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    async def save_survey_response(self, data: Dict[str, Any]) -> bool:
        """So'rovnoma javobini saqlash"""
        try:
            async with self.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO survey_responses (
                        user_id, unique_id, fullname, group_name,
                        phone, permanent_address, permanent_location, previous_education, document_number,
                        has_achievements, achievements,
                        has_certificate, certificate_type, certificate_details, certificate_file,
                        has_grant, grant_details,
                        social_protection, iron_book, youth_book,
                        father_name, father_alive, father_phone,
                        mother_name, mother_alive, mother_phone, parents_together,
                        living_type, ttj_location, rent_address, rent_location, rent_owner,
                        is_working, workplace, is_married,
                        has_foreign_passport, has_social_channels, social_links
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('user_id'),
                    data.get('unique_id'),
                    data.get('fullname'),
                    data.get('group_name') or data.get('group_number'),
                    data.get('phone'),
                    data.get('permanent_address'),
                    data.get('permanent_location'),
                    data.get('previous_education'),
                    data.get('document_number'),
                    data.get('has_achievements'),
                    data.get('achievements'),
                    data.get('has_certificate'),
                    data.get('certificate_type'),
                    data.get('certificate_details'),
                    data.get('certificate_file'),
                    data.get('has_grant'),
                    data.get('grant_details'),
                    data.get('social_protection'),
                    data.get('iron_book'),
                    data.get('youth_book'),
                    data.get('father_name'),
                    data.get('father_alive'),
                    data.get('father_phone'),
                    data.get('mother_name'),
                    data.get('mother_alive'),
                    data.get('mother_phone'),
                    data.get('parents_together'),
                    data.get('living_type'),
                    data.get('ttj_location'),
                    data.get('rent_address'),
                    data.get('rent_location'),
                    data.get('rent_owner'),
                    data.get('is_working'),
                    data.get('workplace'),
                    data.get('is_married'),
                    data.get('has_foreign_passport'),
                    data.get('has_social_channels'),
                    data.get('social_links')
                ))
                return True
        except Exception as e:
            print(f"Error saving survey: {e}")
            return False
    
    async def get_all_students(self) -> List[Dict]:
        """Barcha talabalarni olish"""
        async with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM students ORDER BY id")
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_all_responses(self) -> List[Dict]:
        """Barcha so'rovnoma javoblarini olish"""
        async with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT sr.*, 
                       s.talaba_id, s.citizenship, s.country, s.nationality,
                       s.region, s.district, s.gender, s.birth_date, s.passport,
                       s.jshshir, s.passport_date, s.course, s.faculty,
                       s.language, s.study_year, s.semester, s.graduate,
                       s.specialty, s.education_type, s.education_form,
                       s.payment_type, s.grant_type, s.student_category,
                       s.social_category, s.family_members
                FROM survey_responses sr
                LEFT JOIN students s ON sr.unique_id = s.unique_id
                ORDER BY sr.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
    
    async def get_statistics(self) -> Dict[str, int]:
        """Statistika"""
        async with self.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM students")
            total_students = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM survey_responses")
            completed_surveys = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM staff")
            total_staff = cursor.fetchone()['count']
            
            return {
                'total_students': total_students,
                'completed_surveys': completed_surveys,
                'total_staff': total_staff
            }
    
    async def clear_all_surveys(self) -> int:
        """Barcha so'rovnoma javoblarini o'chirish"""
        try:
            async with self.get_cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM survey_responses")
                count = cursor.fetchone()['count']
                cursor.execute("DELETE FROM survey_responses")
                return count
        except Exception as e:
            print(f"Error clearing surveys: {e}")
            return 0
    
    async def add_student(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Talaba qo'shish yoki yangilash"""
        try:
            async with self.get_cursor() as cursor:
                passport = data.get('passport', '')
                jshshir = data.get('jshshir', '')
                talaba_id = data.get('talaba_id', '')
                
                existing = None
                
                # Passport bo'yicha qidirish
                if passport:
                    cursor.execute("SELECT * FROM students WHERE passport = ?", (passport,))
                    existing = cursor.fetchone()
                
                # JSHSHIR bo'yicha qidirish
                if not existing and jshshir:
                    cursor.execute("SELECT * FROM students WHERE jshshir = ?", (jshshir,))
                    existing = cursor.fetchone()
                
                # Talaba ID bo'yicha qidirish
                if not existing and talaba_id:
                    cursor.execute("SELECT * FROM students WHERE talaba_id = ?", (talaba_id,))
                    existing = cursor.fetchone()
                
                if existing:
                    # Yangilash
                    cursor.execute("""
                        UPDATE students SET
                            talaba_id = COALESCE(?, talaba_id),
                            fullname = COALESCE(?, fullname),
                            citizenship = COALESCE(?, citizenship),
                            country = COALESCE(?, country),
                            nationality = COALESCE(?, nationality),
                            region = COALESCE(?, region),
                            district = COALESCE(?, district),
                            gender = COALESCE(?, gender),
                            birth_date = COALESCE(?, birth_date),
                            passport = COALESCE(?, passport),
                            jshshir = COALESCE(?, jshshir),
                            passport_date = COALESCE(?, passport_date),
                            course = COALESCE(?, course),
                            faculty = COALESCE(?, faculty),
                            group_name = COALESCE(?, group_name),
                            language = COALESCE(?, language),
                            study_year = COALESCE(?, study_year),
                            semester = COALESCE(?, semester),
                            graduate = COALESCE(?, graduate),
                            specialty = COALESCE(?, specialty),
                            education_type = COALESCE(?, education_type),
                            education_form = COALESCE(?, education_form),
                            payment_type = COALESCE(?, payment_type),
                            grant_type = COALESCE(?, grant_type),
                            previous_education = COALESCE(?, previous_education),
                            student_category = COALESCE(?, student_category),
                            social_category = COALESCE(?, social_category),
                            family_members = COALESCE(?, family_members),
                            phone = COALESCE(?, phone),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (
                        data.get('talaba_id'),
                        data.get('fullname'),
                        data.get('citizenship'),
                        data.get('country'),
                        data.get('nationality'),
                        data.get('region'),
                        data.get('district'),
                        data.get('gender'),
                        data.get('birth_date'),
                        data.get('passport'),
                        data.get('jshshir'),
                        data.get('passport_date'),
                        data.get('course'),
                        data.get('faculty'),
                        data.get('group_name'),
                        data.get('language'),
                        data.get('study_year'),
                        data.get('semester'),
                        data.get('graduate'),
                        data.get('specialty'),
                        data.get('education_type'),
                        data.get('education_form'),
                        data.get('payment_type'),
                        data.get('grant_type'),
                        data.get('previous_education'),
                        data.get('student_category'),
                        data.get('social_category'),
                        data.get('family_members'),
                        data.get('phone'),
                        existing['id']
                    ))
                    return {'action': 'updated', 'unique_id': existing['unique_id']}
                else:
                    # Yangi unikal ID
                    unique_id = await self.get_next_unique_id()
                    
                    cursor.execute("""
                        INSERT INTO students (
                            unique_id, talaba_id, fullname, citizenship, country, nationality,
                            region, district, gender, birth_date, passport, jshshir, passport_date,
                            course, faculty, group_name, language, study_year, semester, graduate,
                            specialty, education_type, education_form, payment_type, grant_type,
                            previous_education, student_category, social_category, family_members, phone
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        unique_id,
                        data.get('talaba_id'),
                        data.get('fullname'),
                        data.get('citizenship'),
                        data.get('country'),
                        data.get('nationality'),
                        data.get('region'),
                        data.get('district'),
                        data.get('gender'),
                        data.get('birth_date'),
                        data.get('passport'),
                        data.get('jshshir'),
                        data.get('passport_date'),
                        data.get('course'),
                        data.get('faculty'),
                        data.get('group_name'),
                        data.get('language'),
                        data.get('study_year'),
                        data.get('semester'),
                        data.get('graduate'),
                        data.get('specialty'),
                        data.get('education_type'),
                        data.get('education_form'),
                        data.get('payment_type'),
                        data.get('grant_type'),
                        data.get('previous_education'),
                        data.get('student_category'),
                        data.get('social_category'),
                        data.get('family_members'),
                        data.get('phone')
                    ))
                    return {'action': 'added', 'unique_id': unique_id}
        except Exception as e:
            print(f"Error adding student: {e}")
            return {'action': 'error', 'error': str(e)}
    
    async def is_staff(self, telegram_id: int) -> bool:
        """Xodim tekshirish"""
        async with self.get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM staff WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone() is not None
    
    async def add_staff(self, telegram_id: int, fullname: str = None) -> bool:
        """Xodim qo'shish"""
        try:
            async with self.get_cursor() as cursor:
                cursor.execute(
                    "INSERT OR IGNORE INTO staff (telegram_id, fullname) VALUES (?, ?)",
                    (telegram_id, fullname)
                )
                return cursor.rowcount > 0
        except Exception:
            return False
    
    async def remove_staff(self, telegram_id: int) -> bool:
        """Xodim o'chirish"""
        try:
            async with self.get_cursor() as cursor:
                cursor.execute("DELETE FROM staff WHERE telegram_id = ?", (telegram_id,))
                return cursor.rowcount > 0
        except Exception:
            return False
    
    def close(self):
        """Connection yopish"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
