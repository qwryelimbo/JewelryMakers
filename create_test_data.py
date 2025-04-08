from app import app, db, User, Cassette
import os

def create_test_data():
    with app.app_context():
        # Create admin user
        admin = User(username='admin', email='admin@randomplay.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create test cassettes
        cassettes = [
            {
                'title': 'Первая горсть земли',
                'description': 'Захватывающая история о первых шагах человечества в освоении космоса.',
                'release_year': 1985,
                'genre': 'Научная фантастика',
                'price': 5.99,
                'image_path': 'cassettes/First_Piece_of_Soil.png'
            },
            {
                'title': 'Гид по Риду',
                'description': 'Документальный фильм о жизни и творчестве великого писателя.',
                'release_year': 1992,
                'genre': 'Документальный',
                'price': 4.99,
                'image_path': 'cassettes/The_Ridu_Tour.png'
            },
            {
                'title': 'Небытие',
                'description': 'Философская драма о поисках смысла жизни в современном мире.',
                'release_year': 1988,
                'genre': 'Драма',
                'price': 6.99,
                'image_path': 'cassettes/Nihility.png'
            },
            {
                'title': 'Эфирные грёзы',
                'description': 'Сюрреалистическое путешествие в мир снов и фантазий.',
                'release_year': 1995,
                'genre': 'Фэнтези',
                'price': 7.99,
                'image_path': 'cassettes/Enter_the_Ether.png'
            },
            {
                'title': 'Остаться на чашечку кофе',
                'description': 'Романтическая комедия о случайной встрече, изменившей две жизни.',
                'release_year': 1990,
                'genre': 'Романтика',
                'price': 5.49,
                'image_path': 'cassettes/Coffee_Mate.png'
            },
            {
                'title': 'Пространственный мушкетёр',
                'description': 'Приключенческий боевик о герое, сражающемся за справедливость в далёком будущем.',
                'release_year': 1993,
                'genre': 'Боевик',
                'price': 6.49,
                'image_path': 'cassettes/Dimensional_Musketeer.png'
            },
            {
                'title': 'Рейдеры каверн',
                'description': 'Экшн-триллер о группе исследователей, заблудившихся в подземных пещерах.',
                'release_year': 1991,
                'genre': 'Приключения',
                'price': 5.99,
                'image_path': 'cassettes/Raiders_of_the_Hollow.png'
            }
        ]
        
        for cassette_data in cassettes:
            cassette = Cassette(**cassette_data)
            db.session.add(cassette)
        
        # Commit all changes
        db.session.commit()
        print("Test data has been created successfully!")

if __name__ == '__main__':
    create_test_data() 