Пояснительная записка
Кан Артур

Проект: создание игры "Курица-воин" в жанре Roguelike,
реализованной на языке программирования Python с использованием библиотеки Pygame

Данный проект представляет собой игру в жанре Roguelike и обладает основными свойствами данного жанра:
-   Случайная генерация уровня
-   Пошаговость
-   Необратимость смерти персонажа

Все игровые события, содержащие случайный выбор, реализованы с помощью библиотеки random

Игра представляет собой только один уровень, содержащий 12 комнат.
Карта уровня представляет собой матрицу 3 на 4, из которых:
-   Стартовая комната, всегда одинаковая
-   9 комнат, каждая из которых выбирается случайно из шаблоков комнат. В каждой комнате присутствует минимум один враг.
    Если игрок выходит из комнаты, не убив всех врагов, то при перезаходе в данную комнату все враги восстановятся
-   2 комнаты с сокровищем. Первая сокровищница выдаёт игроку новое случаное оружие. Эта сокровищница
    открывается после очистки 4 комнат уровня. Другая сокровищница лечит игрока до 6 - 9 единиц здоровья.
    Эта сокровищница откроется после очистки 6 комнат. Каждая сокровищница может быть использована
    только один раз. Сокровищницы тоже считаются за зачищенные комнаты после их использования
-   Комната босса, всегда одинаковая. Вариаций босса нет, комната не имеет выходов.
    Открывается после зачистки всей карты

Игрок видит карту уровня, в которой показано текущее расположение игрока, сокровищниц, босса,
а также зачищенные комнаты.

Изначально все шаблоны обычных комнат имеют выходы во все стороны.
При инициализации карты все выходы, ведущие за границы карты, блокируются.

Все шаблоны комнат были созданы с помощью Tiled
Использование шаблонов реализовано через библиотеку pytmx

Игрок может передвигаться как на клавиши стрелок, так и на клавиши wasd, на зажатие кнопки пробела производится атака.
Изначально игроку дается 6 единиц здоровья. Пополнить их можно только во второй сокровищнице.
Также игроку со старта выдается обыкновенный меч.

В игре присутствует 5 видов оружия:
 ⁃  Меч, маленький урон перед игроком
 ⁃  Топор, большой урон по площади перед игроком
 ⁃  Копье, небольшой урон на большое расстояние
 ⁃  Посох, средний урон вокруг игрока
 ⁃  Крутой меч, большой урон перед игроком

Игрок может получит одно из четырех последних видов оружия случайно в первой сокровищнице.

В игре существует 5 разных врагов:
 ⁃  Ворона, 5 здоровья, появляется в обычных комнатах, следует за игроком
 ⁃  Стог сена, свернутый в рулон (скирд), 3 здоровья, появляется в обычных комнатах,
    передвигается по диагоналям, отскакивая от препятствий
 ⁃  Пугало, 230 здоровья, является боссом. В первой фазе ходит вокруг точки, являющейся центром комнаты,
    и призывает ворон, во второй фазе следует за игроком
 ⁃  Стог сена для битвы с боссом, 999 здоровья, неубиваемое препятствие, усложняющее битву с боссом.
    Двигается только по горизонтали, отскакивая от стен
 ⁃  Вилы, 999 здоровья, неубиваемое препятствие, усложняющее битву с боссом. Стоят в одной точке.
    Имеет три состояния: ничего нет, предупреждение, атака. Три состояние сменяют друг друга за
    равные промежутки времени. Игрока ранит, только находясь в третьем состоянии

Информация о врагах и видах оружия хранится в специальных файлах json

Для украшения в игре есть различные частицы, которые возникают при смерти врага, смерти игрока, получении игроком урона

Игра имеет заставку, обучение, экран победы и экран поражения

В игре присутствует музыкальное и звуковое сопровождение

Игра ведёт счёт игрока, который показывается в случае прохождения игры. Счёт считается следющим образом:
После зачистки комнаты прибавляется кол-во врагов, которые были в этой комнате, умноженное на 1000
Если игрок получает урон, то из счёта отнимается 500 очков
После победы над боссом к счёту прибавляется оставшееся кол-во очков здоровья, умноежнное на 1000