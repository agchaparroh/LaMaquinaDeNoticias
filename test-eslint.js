// Este archivo tiene errores intencionales para probar ESLint
const mensaje = 'Hola mundo';  // Falta punto y coma
const numero = 42;  // Usa var en lugar de const/let
const mal_indentado = true;  // Mal indentado

function test() {
  console.log('Comillas simples');  // Indentación incorrecta
  console.log('Comillas dobles');  // Debería usar comillas simples
}

if (true) {console.log('Sin espacios');}  // Mal formato