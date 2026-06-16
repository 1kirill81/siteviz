function doPost(e) {
  try {
    var doc = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = doc.getSheets()[0]; // Берем первый лист таблицы
    
    // Получаем данные из параметров запроса
    var name = e.parameter.name;
    var contact = e.parameter.contact;
    var services = e.parameter.services;     // Список всех выбранных услуг
    var totalPrice = e.parameter.total_price; // Итоговая сумма
    var info = e.parameter.info;             // Дополнительная информация
    
    // Добавляем строку в таблицу
    // Порядок колонок: Дата, Имя, Контакт, Услуги, Цена, Инфо
    sheet.appendRow([
      new Date(), 
      name, 
      contact, 
      services, 
      totalPrice, 
      info
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({"result": "success"}))
                         .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({"result": "error", "error": error.toString()}))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}