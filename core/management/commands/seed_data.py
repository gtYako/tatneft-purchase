"""
Populate DB with rich demo data for the oil procurement system.
Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import date, timedelta
import random
from decimal import Decimal

from core.models import (
    CustomUser, Category, Material, WarehouseStock,
    Supplier, PriceQuote, PurchaseRequest, RequestItem,
    PurchaseOrder, AuditLog
)


class Command(BaseCommand):
    help = 'Загружает демонстрационные данные'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Очистка существующих данных...'))
        AuditLog.objects.all().delete()
        PurchaseOrder.objects.all().delete()
        RequestItem.objects.all().delete()
        PurchaseRequest.objects.all().delete()
        PriceQuote.objects.all().delete()
        WarehouseStock.objects.all().delete()
        Material.objects.all().delete()
        Category.objects.all().delete()
        Supplier.objects.all().delete()
        CustomUser.objects.all().delete()

        # ─── Users ───
        pwd = make_password('demo1234')
        users = {
            'admin': CustomUser.objects.create(
                username='admin', password=pwd, role='admin',
                first_name='Иван', last_name='Администратов',
                email='admin@neft.ru', department='ИТ-отдел',
                position='Системный администратор', is_staff=True, is_superuser=True
            ),
            'initiator': CustomUser.objects.create(
                username='initiator', password=pwd, role='initiator',
                first_name='Сергей', last_name='Нефтяников',
                email='initiator@neft.ru', department='Буровой цех №3',
                position='Мастер буровых работ'
            ),
            'purchaser': CustomUser.objects.create(
                username='purchaser', password=pwd, role='purchaser',
                first_name='Ольга', last_name='Закупщикова',
                email='purchaser@neft.ru', department='Отдел снабжения',
                position='Ведущий специалист по закупкам'
            ),
            'analyst': CustomUser.objects.create(
                username='analyst', password=pwd, role='analyst',
                first_name='Алексей', last_name='Аналитиков',
                email='analyst@neft.ru', department='Планово-экономический отдел',
                position='Аналитик закупочной деятельности'
            ),
            'manager': CustomUser.objects.create(
                username='manager', password=pwd, role='manager',
                first_name='Владимир', last_name='Руководителев',
                email='manager@neft.ru', department='Дирекция по МТО',
                position='Начальник отдела МТО'
            ),
        }
        self.stdout.write(self.style.SUCCESS(f'  Пользователей: {len(users)}'))

        # ─── Categories ───
        cats_data = [
            ('Трубы и арматура', 'Трубная продукция, запорная арматура, фитинги'),
            ('Насосное оборудование', 'Центробежные, погружные, плунжерные насосы и насосные агрегаты'),
            ('Электрооборудование', 'Электродвигатели, кабельная продукция, шкафы управления, ВЧП'),
            ('КИП и автоматика', 'Датчики давления, температуры, расходомеры, контроллеры, средства телеметрии'),
            ('Химические реагенты', 'Деэмульгаторы, ингибиторы коррозии и солеотложения, биоциды'),
            ('Крепёж и уплотнения', 'Болты, гайки, шпильки, прокладки, манжеты, сальники'),
            ('Смазочные материалы', 'Масла индустриальные, пластичные смазки, технические жидкости'),
            ('Запасные части', 'ЗИП для ремонта насосного, механического и электрооборудования'),
            ('Изоляционные материалы', 'Теплоизоляция, антикоррозионные покрытия, изоляционные ленты'),
        ]
        categories = {}
        for name, desc in cats_data:
            categories[name] = Category.objects.create(name=name, description=desc)
        self.stdout.write(self.style.SUCCESS(f'  Категорий: {len(categories)}'))

        # ─── Materials ───
        materials_data = [
            ('МТР-001', 'Труба НКТ 73×5,5 мм, сталь 45, ГОСТ 633-80', 'Трубы и арматура', 'шт', 'ГОСТ 633-80', 'Ø73мм, толщ. стенки 5,5мм, длина 10м', 'critical', Decimal('50')),
            ('МТР-002', 'Труба НКТ 89×6,5 мм, сталь 45, ГОСТ 633-80', 'Трубы и арматура', 'шт', 'ГОСТ 633-80', 'Ø89мм, толщ. стенки 6,5мм, длина 10м', 'critical', Decimal('30')),
            ('МТР-003', 'Задвижка клиновая Ду100 Ру16, ст. 20', 'Трубы и арматура', 'шт', 'ГОСТ 5762-2002', 'Ду100, Ру16, фланцевое соединение, УХЛ1', 'high', Decimal('5')),
            ('МТР-004', 'Кран шаровый Ду50 Ру40', 'Трубы и арматура', 'шт', 'ГОСТ 21345-2014', 'Ду50, Ру40, полнопроходной', 'medium', Decimal('10')),
            ('МТР-005', 'Клапан обратный Ду80 Ру16', 'Трубы и арматура', 'шт', 'ГОСТ 27477-87', 'Ду80, Ру16, поворотный', 'medium', Decimal('5')),
            ('МТР-010', 'ЭЦН Reda 250-1200 (погружной насос)', 'Насосное оборудование', 'шт', 'ТУ 3665-001', 'Подача 250 м³/сут, напор 1200 м', 'critical', Decimal('2')),
            ('МТР-011', 'Насос центробежный НМ 1250-260', 'Насосное оборудование', 'шт', 'ГОСТ 22247-96', 'Подача 1250 м³/ч, напор 260 м', 'high', Decimal('1')),
            ('МТР-012', 'Насос плунжерный НП-25 для закачки реагентов', 'Насосное оборудование', 'шт', 'ТУ 26-06-1425', 'Подача 25 л/ч, давление 25 МПа', 'medium', Decimal('2')),
            ('МТР-020', 'Электродвигатель ПЭД-90 (для ЭЦН)', 'Электрооборудование', 'шт', 'ТУ 3664-015', 'Мощность 90 кВт, 2916 об/мин', 'critical', Decimal('2')),
            ('МТР-021', 'Кабель КПБП 3×16 (кабельная линия ЭЦН)', 'Электрооборудование', 'м', 'ТУ 16.К73-05', 'Сечение 3×16 мм², бронированный', 'critical', Decimal('1000')),
            ('МТР-022', 'Шкаф управления УЭЦН (SCADA)', 'Электрооборудование', 'шт', 'ТУ 3425-001', 'Трансформатор 100кВА, IP54', 'high', Decimal('1')),
            ('МТР-023', 'Электродвигатель АИР132S4 (5,5 кВт)', 'Электрооборудование', 'шт', 'ГОСТ Р 51689', 'Мощность 5,5 кВт, 1450 об/мин', 'medium', Decimal('3')),
            ('МТР-030', 'Датчик давления Метран-150 (0-25 МПа)', 'КИП и автоматика', 'шт', 'ТУ 4212-001', 'Диапазон 0-25 МПа, ExdIIBT4', 'high', Decimal('5')),
            ('МТР-031', 'Датчик температуры ТСПУ 9201-0', 'КИП и автоматика', 'шт', 'ГОСТ 6651-2009', 'Диапазон -50...+150°C', 'medium', Decimal('10')),
            ('МТР-032', 'Расходомер электромагнитный ПРЭМ-50', 'КИП и автоматика', 'шт', 'ТУ 4213-006', 'Ду50, Ру16, диапазон 5-300 м³/ч', 'high', Decimal('2')),
            ('МТР-033', 'Контроллер ПЛК Siemens S7-300', 'КИП и автоматика', 'шт', 'EN 61131-3', 'CPU314C-2PN/DP, 24DI/16DO', 'high', Decimal('1')),
            ('МТР-040', 'Деэмульгатор Dissolvan 4411', 'Химические реагенты', 'л', 'ТУ 2458-034', 'Концентрат, расход 30-80 г/т нефти', 'high', Decimal('200')),
            ('МТР-041', 'Ингибитор коррозии Кор-1 (водный р-р)', 'Химические реагенты', 'л', 'ТУ 2458-041', 'Пленкообразующий, дозировка 50-100 мг/л', 'high', Decimal('500')),
            ('МТР-042', 'Антиасфальтеновый реагент АСПО-Д', 'Химические реагенты', 'кг', 'ТУ 2458-015', 'Дозировка 0.05-0.3% от добычи', 'medium', Decimal('100')),
            ('МТР-043', 'Метанол технический (ГОСТ 2222-95)', 'Химические реагенты', 'т', 'ГОСТ 2222-95', 'Квалификация техн., антигидратный', 'critical', Decimal('5')),
            ('МТР-050', 'Шпилька М20×100 ст. 40Х (ГОСТ 22032)', 'Крепёж и уплотнения', 'шт', 'ГОСТ 22032-76', 'М20, длина 100мм, прочность 8.8', 'low', Decimal('100')),
            ('МТР-051', 'Прокладка паронитовая ПОН-Б 10×100×100', 'Крепёж и уплотнения', 'шт', 'ГОСТ 481-80', 'Паронит нефтемаслостойкий', 'medium', Decimal('50')),
            ('МТР-052', 'Манжета резиновая V-образная 50×65×8', 'Крепёж и уплотнения', 'шт', 'ГОСТ 14896-84', 'Резина маслобензостойкая МБС', 'medium', Decimal('20')),
            ('МТР-060', 'Масло турбинное ТП-22С (бочка 216 л)', 'Смазочные материалы', 'л', 'ГОСТ 9972-74', 'Вязкость 20-23 сСт при 50°C', 'low', Decimal('200')),
            ('МТР-061', 'Литол-24 (пластичная смазка, ведро 8 кг)', 'Смазочные материалы', 'кг', 'ГОСТ 21150-87', 'Темп. применения -40...+120°C', 'low', Decimal('20')),
            ('МТР-070', 'Рабочее колесо для ЭЦН Reda 250 (ступень)', 'Запасные части', 'шт', 'ТУ 3665-002', 'Совместимо с ЭЦН Reda 250', 'critical', Decimal('10')),
            ('МТР-071', 'Защита ПЭД-90 (гидрозащита погружного насоса)', 'Запасные части', 'шт', 'ТУ 3664-016', 'Протектор-компенсатор для ПЭД-90', 'critical', Decimal('3')),
            ('МТР-072', 'Торцевое уплотнение для насоса НМ 1250', 'Запасные части', 'шт', 'ТУ 3619-001', 'Комплект торцевого уплотнения', 'high', Decimal('2')),
            ('МТР-080', 'Лента изоляционная ПВХ (рулон 19мм×20м)', 'Изоляционные материалы', 'шт', 'ГОСТ 16214-86', 'Электроизоляционная, черная', 'low', Decimal('100')),
            ('МТР-081', 'Покрытие антикоррозионное Мастика МБИ-90', 'Изоляционные материалы', 'кг', 'ТУ 2513-010', 'Битумно-полимерная, для трубопроводов', 'medium', Decimal('50')),
        ]
        mat_objects = {}
        for code, name, cat_name, unit, gost, specs, crit, min_stock in materials_data:
            m = Material.objects.create(
                code=code, name=name, category=categories[cat_name],
                unit=unit, gost=gost, technical_specs=specs,
                criticality=crit, min_stock_level=min_stock, is_active=True
            )
            mat_objects[code] = m
        self.stdout.write(self.style.SUCCESS(f'  Материалов МТР: {len(mat_objects)}'))

        # ─── Warehouse ───
        stock_data = [
            ('МТР-001', 'Склад ГСМ-1 (площадка А)', Decimal('80'), Decimal('20')),
            ('МТР-002', 'Склад ГСМ-1 (площадка А)', Decimal('25'), Decimal('5')),
            ('МТР-003', 'Склад арматуры (секция 3)', Decimal('3'), Decimal('0')),
            ('МТР-004', 'Склад арматуры (секция 3)', Decimal('12'), Decimal('2')),
            ('МТР-010', 'Склад УЭЦН (площадка Б)', Decimal('1'), Decimal('1')),
            ('МТР-011', 'Склад насосного оборудования', Decimal('0'), Decimal('0')),
            ('МТР-020', 'Склад УЭЦН (площадка Б)', Decimal('1'), Decimal('0')),
            ('МТР-021', 'Склад кабельной продукции', Decimal('500'), Decimal('200')),
            ('МТР-023', 'Склад электрооборудования', Decimal('4'), Decimal('1')),
            ('МТР-030', 'Склад КИП (стеллаж А-4)', Decimal('3'), Decimal('0')),
            ('МТР-031', 'Склад КИП (стеллаж А-4)', Decimal('15'), Decimal('0')),
            ('МТР-040', 'Склад химреагентов (резервуар Х-1)', Decimal('150'), Decimal('0')),
            ('МТР-041', 'Склад химреагентов (резервуар Х-2)', Decimal('300'), Decimal('0')),
            ('МТР-043', 'Склад химреагентов (резервуар Х-3)', Decimal('2'), Decimal('0')),
            ('МТР-050', 'Общий склад МТР (стеллаж 12)', Decimal('200'), Decimal('0')),
            ('МТР-051', 'Общий склад МТР (стеллаж 12)', Decimal('80'), Decimal('10')),
            ('МТР-052', 'Общий склад МТР (стеллаж 13)', Decimal('15'), Decimal('0')),
            ('МТР-060', 'Склад ГСМ-2', Decimal('400'), Decimal('0')),
            ('МТР-061', 'Склад ГСМ-2', Decimal('40'), Decimal('0')),
            ('МТР-070', 'Склад запасных частей (ЗИП-1)', Decimal('5'), Decimal('3')),
            ('МТР-071', 'Склад запасных частей (ЗИП-1)', Decimal('1'), Decimal('1')),
            ('МТР-072', 'Склад запасных частей (ЗИП-1)', Decimal('0'), Decimal('0')),
            ('МТР-080', 'Общий склад МТР (стеллаж 8)', Decimal('150'), Decimal('0')),
            ('МТР-081', 'Склад изоляционных материалов', Decimal('30'), Decimal('0')),
        ]
        for code, loc, qty, reserved in stock_data:
            if code in mat_objects:
                WarehouseStock.objects.create(
                    material=mat_objects[code], location=loc,
                    qty_on_hand=qty, qty_reserved=reserved
                )
        self.stdout.write(self.style.SUCCESS(f'  Складских записей: {len(stock_data)}'))

        # ─── Suppliers ───
        suppliers_data = [
            ('НефтеКомплект', '7720123456', 'Петров А.В.', '+7-495-123-45-67', 'sales@nk.ru',
             'г. Москва, ул. Нефтяников, 15', Decimal('8.5'), Decimal('96.0'), 'Крупный поставщик МТР для нефтянки'),
            ('ТехноПромГрупп', '6670987654', 'Сидорова Н.П.', '+7-343-456-78-90', 'tpg@gmail.com',
             'г. Екатеринбург, ул. Машиностроителей, 8', Decimal('7.0'), Decimal('88.0'), 'Поставщик труб и арматуры'),
            ('ИнтерХим Урал', '6602345678', 'Зимин Д.С.', '+7-342-567-89-01', 'order@interchem.ru',
             'г. Пермь, ул. Химиков, 3', Decimal('9.0'), Decimal('98.5'), 'Специализируется на химреагентах'),
            ('Восток-МТР', '7201234567', 'Кузьмин Л.А.', '+7-3452-345-67-89', 'vmtr@inbox.ru',
             'г. Тюмень, ул. Нефтяной путь, 22', Decimal('6.5'), Decimal('82.0'), 'Региональный поставщик'),
            ('ЭлектроМаш', '7741234567', 'Белова О.К.', '+7-495-987-65-43', 'sales@emash.ru',
             'г. Москва, ул. Электрозаводская, 1', Decimal('8.0'), Decimal('94.0'), 'Электрооборудование и КИП'),
            ('УралТрансНефть', '6671234567', 'Романов В.Р.', '+7-343-678-90-12', 'utn@mail.ru',
             'г. Екатеринбург, пр-т Ленина, 54', Decimal('7.5'), Decimal('91.0'), 'Трубопроводная продукция'),
        ]
        supplier_objects = []
        for name, inn, contact, phone, email, addr, rating, reliability, notes in suppliers_data:
            s = Supplier.objects.create(
                name=name, inn=inn, contact_person=contact, phone=phone,
                email=email, address=addr, rating=rating,
                delivery_reliability=reliability, notes=notes, is_active=True
            )
            supplier_objects.append(s)
        self.stdout.write(self.style.SUCCESS(f'  Поставщиков: {len(supplier_objects)}'))

        # ─── Price Quotes (rich historical data for charts) ───
        today = date.today()

        def make_price_series(code, sup_idx, base_price, trend=1.0, months=12, delivery=14, payment='По счёту'):
            """Generate monthly price quotes over past N months with slight variation."""
            mat = mat_objects.get(code)
            sup = supplier_objects[sup_idx] if sup_idx < len(supplier_objects) else supplier_objects[0]
            if mat is None:
                return
            for i in range(months, 0, -1):
                dt = today - timedelta(days=30 * i)
                # Price grows with trend + random ±5%
                noise = random.uniform(0.95, 1.05)
                growth = trend ** (months - i)
                price = round(Decimal(str(float(base_price) * growth * noise)), 2)
                PriceQuote.objects.create(
                    material=mat, supplier=sup, price=price,
                    delivery_days=delivery, payment_terms=payment,
                    quote_date=dt, valid_until=dt + timedelta(days=30),
                    notes=''
                )

        # НКТ 73 — 3 поставщика, 12 месяцев истории
        make_price_series('МТР-001', 0, 16000, trend=1.012, months=12, delivery=14, payment='По счёту 30 дней')
        make_price_series('МТР-001', 1, 15500, trend=1.008, months=12, delivery=21, payment='Предоплата 50%')
        make_price_series('МТР-001', 5, 17000, trend=1.015, months=12, delivery=10, payment='Предоплата 100%')
        # Свежие актуальные КП
        PriceQuote.objects.create(material=mat_objects['МТР-001'], supplier=supplier_objects[0],
            price=Decimal('18500'), delivery_days=14, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=5), valid_until=today + timedelta(days=30))
        PriceQuote.objects.create(material=mat_objects['МТР-001'], supplier=supplier_objects[1],
            price=Decimal('17200'), delivery_days=21, payment_terms='Предоплата 50%',
            quote_date=today - timedelta(days=30), valid_until=today + timedelta(days=10))

        # НКТ 89
        make_price_series('МТР-002', 0, 22000, trend=1.010, months=12, delivery=14)
        make_price_series('МТР-002', 1, 21000, trend=1.007, months=12, delivery=25)
        PriceQuote.objects.create(material=mat_objects['МТР-002'], supplier=supplier_objects[0],
            price=Decimal('24500'), delivery_days=14, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=3), valid_until=today + timedelta(days=30))

        # ЭЦН — дорогое оборудование, сильный рост
        make_price_series('МТР-010', 0, 680000, trend=1.018, months=18, delivery=45)
        make_price_series('МТР-010', 3, 650000, trend=1.015, months=18, delivery=60)
        make_price_series('МТР-010', 4, 780000, trend=1.020, months=18, delivery=30)
        PriceQuote.objects.create(material=mat_objects['МТР-010'], supplier=supplier_objects[0],
            price=Decimal('850000'), delivery_days=45, payment_terms='По счёту 60 дней',
            quote_date=today - timedelta(days=7), valid_until=today + timedelta(days=23))
        PriceQuote.objects.create(material=mat_objects['МТР-010'], supplier=supplier_objects[4],
            price=Decimal('920000'), delivery_days=30, payment_terms='Постоплата 45 дней',
            quote_date=today - timedelta(days=2), valid_until=today + timedelta(days=28))

        # ПЭД-90
        make_price_series('МТР-020', 4, 250000, trend=1.014, months=12, delivery=20)
        make_price_series('МТР-020', 0, 270000, trend=1.012, months=12, delivery=35)
        PriceQuote.objects.create(material=mat_objects['МТР-020'], supplier=supplier_objects[4],
            price=Decimal('280000'), delivery_days=20, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=5), valid_until=today + timedelta(days=25))

        # Кабель — много точек
        make_price_series('МТР-021', 4, 1400, trend=1.022, months=18, delivery=14)
        make_price_series('МТР-021', 1, 1350, trend=1.018, months=18, delivery=21)
        PriceQuote.objects.create(material=mat_objects['МТР-021'], supplier=supplier_objects[4],
            price=Decimal('1850'), delivery_days=14, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=4), valid_until=today + timedelta(days=26))

        # Датчик давления
        make_price_series('МТР-030', 4, 24000, trend=1.010, months=12, delivery=10)
        make_price_series('МТР-030', 3, 22000, trend=1.008, months=12, delivery=21)
        PriceQuote.objects.create(material=mat_objects['МТР-030'], supplier=supplier_objects[4],
            price=Decimal('28500'), delivery_days=10, payment_terms='По счёту',
            quote_date=today - timedelta(days=6), valid_until=today + timedelta(days=24))

        # Деэмульгатор
        make_price_series('МТР-040', 2, 145, trend=1.025, months=18, delivery=7)
        make_price_series('МТР-040', 3, 165, trend=1.020, months=18, delivery=14)
        PriceQuote.objects.create(material=mat_objects['МТР-040'], supplier=supplier_objects[2],
            price=Decimal('185'), delivery_days=7, payment_terms='По счёту 15 дней',
            quote_date=today - timedelta(days=3), valid_until=today + timedelta(days=27))

        # Ингибитор коррозии
        make_price_series('МТР-041', 2, 78, trend=1.018, months=12, delivery=7)
        make_price_series('МТР-041', 3, 88, trend=1.015, months=12, delivery=14)
        PriceQuote.objects.create(material=mat_objects['МТР-041'], supplier=supplier_objects[2],
            price=Decimal('95'), delivery_days=7, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=2), valid_until=today + timedelta(days=28))

        # Метанол
        make_price_series('МТР-043', 2, 42000, trend=1.030, months=12, delivery=3)
        make_price_series('МТР-043', 3, 40000, trend=1.025, months=12, delivery=7)
        PriceQuote.objects.create(material=mat_objects['МТР-043'], supplier=supplier_objects[2],
            price=Decimal('52000'), delivery_days=3, payment_terms='Предоплата 100%',
            quote_date=today - timedelta(days=1), valid_until=today + timedelta(days=14))

        # Рабочее колесо ЭЦН
        make_price_series('МТР-070', 0, 38000, trend=1.015, months=12, delivery=30)
        make_price_series('МТР-070', 3, 36000, trend=1.012, months=12, delivery=45)
        PriceQuote.objects.create(material=mat_objects['МТР-070'], supplier=supplier_objects[0],
            price=Decimal('45000'), delivery_days=30, payment_terms='По счёту',
            quote_date=today - timedelta(days=10), valid_until=today + timedelta(days=20))

        # Торцевое уплотнение
        make_price_series('МТР-072', 0, 31000, trend=1.014, months=12, delivery=21)
        PriceQuote.objects.create(material=mat_objects['МТР-072'], supplier=supplier_objects[0],
            price=Decimal('38000'), delivery_days=21, payment_terms='По счёту 30 дней',
            quote_date=today - timedelta(days=7), valid_until=today + timedelta(days=23))
        PriceQuote.objects.create(material=mat_objects['МТР-072'], supplier=supplier_objects[4],
            price=Decimal('35500'), delivery_days=28, payment_terms='Предоплата',
            quote_date=today - timedelta(days=3), valid_until=today + timedelta(days=27))

        self.stdout.write(self.style.SUCCESS(f'  Ценовых предложений: {PriceQuote.objects.count()}'))

        # ─── Purchase Requests (12 штук, разные статусы и месяцы) ───
        initiator = users['initiator']
        purchaser = users['purchaser']
        manager   = users['manager']

        def make_request(number, req_user, dept, need_delta, crit, status,
                         justification, rejection='', app_by=None, app_delta=None,
                         created_delta=0):
            approved_at = None
            if app_by and app_delta is not None:
                from django.utils import timezone as tz
                approved_at = tz.now() - timedelta(days=app_delta)
            r = PurchaseRequest(
                request_number=number,
                requester=req_user,
                department=dept,
                need_date=today + timedelta(days=need_delta),
                criticality=crit,
                status=status,
                justification=justification,
                rejection_comment=rejection,
                approved_by=app_by,
                approved_at=approved_at,
            )
            r.save()
            # backdate created_at
            PurchaseRequest.objects.filter(pk=r.pk).update(
                created_at=timezone.now() - timedelta(days=created_delta)
            )
            r.refresh_from_db()
            return r

        q001 = PriceQuote.objects.filter(material=mat_objects['МТР-001']).order_by('price').first()
        q010 = PriceQuote.objects.filter(material=mat_objects['МТР-010'], supplier=supplier_objects[4]).first()
        q020 = PriceQuote.objects.filter(material=mat_objects['МТР-020']).first()
        q040 = PriceQuote.objects.filter(material=mat_objects['МТР-040']).order_by('price').first()
        q041 = PriceQuote.objects.filter(material=mat_objects['МТР-041']).order_by('price').first()
        q043 = PriceQuote.objects.filter(material=mat_objects['МТР-043']).order_by('price').first()
        q070 = PriceQuote.objects.filter(material=mat_objects['МТР-070']).order_by('price').first()
        q072 = PriceQuote.objects.filter(material=mat_objects['МТР-072']).order_by('price').first()
        q021 = PriceQuote.objects.filter(material=mat_objects['МТР-021']).order_by('price').first()

        # 1 — Завершённая, 6 мес. назад
        req1 = make_request('ЗК-2025-0001', initiator, 'Буровой цех №3',
                            -30, 'planned', 'completed',
                            'Плановое пополнение запасов НКТ для бурения скважин на участке 12А.',
                            app_by=manager, app_delta=50, created_delta=180)
        if q001:
            RequestItem.objects.create(request=req1, material=mat_objects['МТР-001'],
                qty_requested=Decimal('20'), qty_available_at_warehouse=Decimal('0'),
                qty_to_purchase=Decimal('20'), target_price=Decimal('18500'),
                selected_quote=q001, justification_for_choice='Лучшее соотношение цена/срок.')
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0001', request=req1, supplier=supplier_objects[0],
            order_date=today - timedelta(days=175), expected_delivery_date=today - timedelta(days=161),
            actual_delivery_date=today - timedelta(days=160), status='delivered',
            total_amount=Decimal('370000'), created_by=purchaser
        )

        # 2 — Аварийная, ordered
        req2 = make_request('ЗК-2025-0002', initiator, 'Буровой цех №3',
                            3, 'emergency', 'ordered',
                            'Аварийный выход из строя ЭЦН на скважине №47, срочная замена.',
                            app_by=manager, app_delta=2, created_delta=30)
        if q010:
            RequestItem.objects.create(request=req2, material=mat_objects['МТР-010'],
                qty_requested=Decimal('1'), qty_available_at_warehouse=Decimal('0'),
                qty_to_purchase=Decimal('1'), target_price=Decimal('920000'),
                selected_quote=q010,
                justification_for_choice='Выбран поставщик с минимальным сроком поставки.')
        RequestItem.objects.create(request=req2, material=mat_objects['МТР-020'],
            qty_requested=Decimal('1'), qty_available_at_warehouse=Decimal('1'),
            qty_to_purchase=Decimal('0'), notes='Есть на складе, резерв создан')
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0002', request=req2, supplier=supplier_objects[4],
            order_date=today - timedelta(days=1), expected_delivery_date=today + timedelta(days=29),
            status='sent', total_amount=Decimal('920000'), created_by=purchaser
        )

        # 3 — На рассмотрении, плановая (химреагенты)
        req3 = make_request('ЗК-2025-0003', initiator, 'Участок подготовки нефти',
                            25, 'planned', 'submitted',
                            'Пополнение запасов химреагентов на 2 квартал.',
                            created_delta=10)
        RequestItem.objects.create(request=req3, material=mat_objects['МТР-040'],
            qty_requested=Decimal('500'), qty_available_at_warehouse=Decimal('150'),
            qty_to_purchase=Decimal('350'), target_price=Decimal('185'))
        RequestItem.objects.create(request=req3, material=mat_objects['МТР-041'],
            qty_requested=Decimal('1000'), qty_available_at_warehouse=Decimal('300'),
            qty_to_purchase=Decimal('700'), target_price=Decimal('95'))
        RequestItem.objects.create(request=req3, material=mat_objects['МТР-043'],
            qty_requested=Decimal('10'), qty_available_at_warehouse=Decimal('2'),
            qty_to_purchase=Decimal('8'), target_price=Decimal('52000'))

        # 4 — Черновик
        req4 = make_request('ЗК-2025-0004', initiator, 'Ремонтно-механическая служба',
                            14, 'planned', 'draft',
                            'Плановый ремонт насоса НМ 1250-260 на ДНС-2.',
                            created_delta=5)
        if q072:
            RequestItem.objects.create(request=req4, material=mat_objects['МТР-072'],
                qty_requested=Decimal('1'), qty_available_at_warehouse=Decimal('0'),
                qty_to_purchase=Decimal('1'))
        RequestItem.objects.create(request=req4, material=mat_objects['МТР-052'],
            qty_requested=Decimal('10'), qty_available_at_warehouse=Decimal('10'),
            qty_to_purchase=Decimal('0'))

        # 5 — Отклонённая
        req5 = make_request('ЗК-2025-0005', initiator, 'Буровой цех №1',
                            60, 'planned', 'rejected',
                            'Дополнительный запас кабеля ЭЦН на складе.',
                            rejection='На складе достаточно. Подать повторно при остатке ниже 500м.',
                            app_by=manager, app_delta=3, created_delta=45)
        RequestItem.objects.create(request=req5, material=mat_objects['МТР-021'],
            qty_requested=Decimal('2000'), qty_available_at_warehouse=Decimal('300'),
            qty_to_purchase=Decimal('1700'))

        # 6 — Аварийная, на рассмотрении
        req6 = make_request('ЗК-2025-0006', initiator, 'Буровой цех №2',
                            5, 'emergency', 'submitted',
                            'Срочно рабочее колесо для ЭЦН на скважине №89.',
                            created_delta=3)
        RequestItem.objects.create(request=req6, material=mat_objects['МТР-070'],
            qty_requested=Decimal('5'), qty_available_at_warehouse=Decimal('2'),
            qty_to_purchase=Decimal('3'), target_price=Decimal('45000'))

        # 7 — Завершённая, 5 мес. назад
        req7 = make_request('ЗК-2025-0007', initiator, 'Цех поддержания давления',
                            -20, 'planned', 'completed',
                            'Закупка датчиков давления для модернизации ДНС-1.',
                            app_by=manager, app_delta=40, created_delta=150)
        RequestItem.objects.create(request=req7, material=mat_objects['МТР-030'],
            qty_requested=Decimal('10'), qty_available_at_warehouse=Decimal('3'),
            qty_to_purchase=Decimal('7'), target_price=Decimal('28500'),
            selected_quote=PriceQuote.objects.filter(material=mat_objects['МТР-030']).first())
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0003', request=req7, supplier=supplier_objects[4],
            order_date=today - timedelta(days=145), expected_delivery_date=today - timedelta(days=130),
            actual_delivery_date=today - timedelta(days=128), status='delivered',
            total_amount=Decimal('199500'), created_by=purchaser
        )

        # 8 — Завершённая, 4 мес. назад
        req8 = make_request('ЗК-2025-0008', initiator, 'Отдел главного механика',
                            -10, 'planned', 'completed',
                            'Пополнение запасов смазочных материалов на летний сезон.',
                            app_by=manager, app_delta=25, created_delta=120)
        RequestItem.objects.create(request=req8, material=mat_objects['МТР-060'],
            qty_requested=Decimal('1000'), qty_available_at_warehouse=Decimal('400'),
            qty_to_purchase=Decimal('600'), target_price=Decimal('95'))
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0004', request=req8, supplier=supplier_objects[0],
            order_date=today - timedelta(days=115), expected_delivery_date=today - timedelta(days=100),
            actual_delivery_date=today - timedelta(days=99), status='delivered',
            total_amount=Decimal('57000'), created_by=purchaser
        )

        # 9 — Утверждённая (ожидает заказа)
        req9 = make_request('ЗК-2025-0009', initiator, 'Буровой цех №3',
                            30, 'planned', 'approved',
                            'Пополнение ЗИП для технического обслуживания УЭЦН.',
                            app_by=manager, app_delta=1, created_delta=15)
        if q070:
            RequestItem.objects.create(request=req9, material=mat_objects['МТР-070'],
                qty_requested=Decimal('8'), qty_available_at_warehouse=Decimal('2'),
                qty_to_purchase=Decimal('6'), target_price=Decimal('45000'),
                selected_quote=q070)
        if q071 := PriceQuote.objects.filter(material=mat_objects['МТР-071']).first():
            RequestItem.objects.create(request=req9, material=mat_objects['МТР-071'],
                qty_requested=Decimal('2'), qty_available_at_warehouse=Decimal('0'),
                qty_to_purchase=Decimal('2'), target_price=Decimal('95000'),
                selected_quote=q071)

        # 10 — Завершённая, 3 мес. назад
        req10 = make_request('ЗК-2025-0010', initiator, 'Участок подготовки нефти',
                             -5, 'planned', 'completed',
                             'Закупка деэмульгатора на 2-й квартал.',
                             app_by=manager, app_delta=15, created_delta=90)
        if q040:
            RequestItem.objects.create(request=req10, material=mat_objects['МТР-040'],
                qty_requested=Decimal('800'), qty_available_at_warehouse=Decimal('150'),
                qty_to_purchase=Decimal('650'), target_price=Decimal('185'),
                selected_quote=q040)
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0005', request=req10, supplier=supplier_objects[2],
            order_date=today - timedelta(days=85), expected_delivery_date=today - timedelta(days=78),
            actual_delivery_date=today - timedelta(days=77), status='delivered',
            total_amount=Decimal('120250'), created_by=purchaser
        )

        # 11 — ordered, 2 мес. назад
        req11 = make_request('ЗК-2025-0011', initiator, 'Электрослужба',
                             20, 'planned', 'ordered',
                             'Закупка кабеля ЭЦН для запасного фонда.',
                             app_by=manager, app_delta=8, created_delta=60)
        if q021:
            RequestItem.objects.create(request=req11, material=mat_objects['МТР-021'],
                qty_requested=Decimal('3000'), qty_available_at_warehouse=Decimal('300'),
                qty_to_purchase=Decimal('2700'), target_price=Decimal('1850'),
                selected_quote=q021)
        PurchaseOrder.objects.create(
            order_number='ЗП-2025-0006', request=req11, supplier=supplier_objects[4],
            order_date=today - timedelta(days=55), expected_delivery_date=today + timedelta(days=5),
            status='confirmed', total_amount=Decimal('4995000'), created_by=purchaser
        )

        # 12 — submitted, прошлый месяц
        req12 = make_request('ЗК-2025-0012', initiator, 'Цех нефтеподготовки',
                             40, 'planned', 'submitted',
                             'Закупка метанола для антигидратной обработки скважин.',
                             created_delta=35)
        RequestItem.objects.create(request=req12, material=mat_objects['МТР-043'],
            qty_requested=Decimal('20'), qty_available_at_warehouse=Decimal('2'),
            qty_to_purchase=Decimal('18'), target_price=Decimal('52000'))

        self.stdout.write(self.style.SUCCESS(
            f'  Заявок: {PurchaseRequest.objects.count()}, '
            f'позиций: {RequestItem.objects.count()}, '
            f'заказов: {PurchaseOrder.objects.count()}'
        ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены!'))
        self.stdout.write('')
        self.stdout.write('Тестовые учётные записи (пароль для всех: demo1234):')
        self.stdout.write('  admin      — Администратор')
        self.stdout.write('  initiator  — Инициатор (Производство)')
        self.stdout.write('  purchaser  — Закупщик (Снабжение)')
        self.stdout.write('  analyst    — Аналитик')
        self.stdout.write('  manager    — Руководитель')
        self.stdout.write(self.style.SUCCESS('=' * 60))
