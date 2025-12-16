def number_to_words_es(n: int) -> str:
    # Simple y suficiente para COP comunes (hasta millones bien).
    units = ["cero","uno","dos","tres","cuatro","cinco","seis","siete","ocho","nueve"]
    tens = ["","diez","veinte","treinta","cuarenta","cincuenta","sesenta","setenta","ochenta","noventa"]
    teens = {11:"once",12:"doce",13:"trece",14:"catorce",15:"quince",16:"dieciséis",17:"diecisiete",18:"dieciocho",19:"diecinueve"}
    hundreds = ["","ciento","doscientos","trescientos","cuatrocientos","quinientos","seiscientos","setecientos","ochocientos","novecientos"]

    if n == 0:
        return "cero"
    if n == 100:
        return "cien"

    def under_100(x: int) -> str:
        if x < 10:
            return units[x]
        if 10 <= x <= 19:
            if x == 10: return "diez"
            return teens[x]
        if x == 20:
            return "veinte"
        if 21 <= x <= 29:
            return "veinti" + units[x-20]
        t = x // 10
        u = x % 10
        if u == 0:
            return tens[t]
        return f"{tens[t]} y {units[u]}"

    def under_1000(x: int) -> str:
        if x < 100:
            return under_100(x)
        if x == 100:
            return "cien"
        h = x // 100
        r = x % 100
        if r == 0:
            return hundreds[h]
        return f"{hundreds[h]} {under_100(r)}"

    # miles
    if n < 1000:
        return under_1000(n)

    if n < 1_000_000:
        m = n // 1000
        r = n % 1000
        if m == 1:
            prefix = "mil"
        else:
            prefix = f"{under_1000(m)} mil"
        if r == 0:
            return prefix
        return f"{prefix} {under_1000(r)}"

    # millones (simple)
    if n < 1_000_000_000:
        mm = n // 1_000_000
        r = n % 1_000_000
        if mm == 1:
            prefix = "un millón"
        else:
            prefix = f"{number_to_words_es(mm)} millones"
        if r == 0:
            return prefix
        return f"{prefix} {number_to_words_es(r)}"

    return str(n)  # fallback

def cop_amount_to_text(amount: int) -> str:
    # “Ciento setenta mil pesos (COP)” etc.
    words = number_to_words_es(amount).strip()
    # Ajuste “uno” -> “un” delante de “mil/millón” ya queda bien en nuestra función en millones; para otros casos, lo dejamos.
    return f"{words} pesos (COP)"
