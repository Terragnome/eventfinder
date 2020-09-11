all_categories = """Market
Market / Asian
Market / Bulk
Market / Butcher
Market / Court
Market / Deli
Market / Farmers
Market / Food Trucks
Market / Fruit
Market / Gourmet
Market / Indian
Market / Italian
Market / Latin
Market / Liquor
Market / Night
Market / Pasta
Market / Russian
Bar
Bar / Casual
Bar / Cocktail
Bar / Pub
Bar / Sports
Bar / Wine
Cafe / Board Game
Cafe / Coffee
Cafe / High Tea
Cafe / PMT
Cafe / Tea
Bakery
Bakery / Asian
Bakery / Bagel
Bakery / Cake
Bakery / Cookie
Bakery / Pie
Bakery / Portuguese
Dessert
Dessert / Chocolate
Dessert / Donuts
Dessert / Ice Cream
Dessert / Mochi
Snack / Fried Chicken
Snack / Wing
African / Egyptian
African / Ethiopian
African / Moroccan
Asian / Chinese
Asian / Chinese / Dim Sum
Asian / Chinese / Dumpling
Asian / Chinese / Hunan
Asian / Chinese / Muslim
Asian / Chinese / Noodle
Asian / Chinese / Sichuan
Asian / Chinese / Taiwanese
Asian / Fusion
Asian / Hot Pot
Asian / Japanese
Asian / Japanese / Curry
Asian / Japanese / Izakaya
Asian / Japanese / Kaiseki
Asian / Japanese / Noodle
Asian / Japanese / Noodle / Ramen
Asian / Japanese / Noodle / Udon
Asian / Japanese / Robata
Asian / Japanese / Sushi
Asian / Japanese / Sushi / Omakase
Asian / Japanese / Sushi / Roll
Asian / Japanese / Teppanyaki
Asian / Japanese / Teshoku
Asian / Japanese / Yakitori
Asian / Korean
Asian / Mongolian
Asian / Noodle
Asian / SEA
Asian / SEA / Burmese
Asian / SEA / Cambodian
Asian / SEA / Filipino
Asian / SEA / Sri Lankan
Asian / SEA / Thai
Asian / SEA / Vietnamese
Asian / SEA / Vietnamese / Bahn Mi
Asian / SEA / Vietnamese / Noodle
Asian / SEA / Vietnamese / Noodle / Pho
Asian / Singaporean
Deli / Canadian
European
European / British
European / French
European / German
European / Italian
European / Italian / Roman
European / Mediterranean
European / Portuguese
European / Scandanavian
I18n
Island / Caribbean
Island / Hawaiian
Latin
Latin / Brazillian
Latin / Mexican
Latin / Peruvian
Latin / Salvadoran
Latin / Spanish
Latin / Spanish / Tapas
Middle Eastern
Slavic
Slavic / Russian
South Asian
Vegetarian
Western / Barbecue
Western / Brunch
Western / Burger & Sandwich
Western / Crepes
Western / Dinner
Western / Fine Dining
Western / Pizza
Western / Pizza / Chicago
Western / Pizza / New York
Western / Salad
Western / Seafood
Western / Seafood / Boil
Western / Southern
Western / Steak""".split("\n")

class Category:
  @classmethod
  def all(cls):
    return all_categories
