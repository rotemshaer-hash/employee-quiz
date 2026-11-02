// לא עושה cache בכוונה — רק קיים כדי שאנדרואיד יציע "הוספה למסך הבית".
// כל בקשה הולכת ישירות לרשת, בלי שמירה מקומית, כדי שלא ניצור שוב את בעיית
// הגרסה הישנה שנתקעת במטמון (ה-?v= בתגיות הסקריפט כבר פותר את זה בפני עצמו).
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {});
