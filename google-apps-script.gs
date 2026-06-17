function doGet(e) {
  try {
    var doc = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = doc.getSheets()[0];
    var data = sheet.getDataRange().getValues();
    
    // Предполагаем, что 1-я строка - заголовок. Берем последние 10 клиентов для примера.
    var clients = [];
    for (var i = 1; i < data.length; i++) {
      clients.push({
        date: data[i][0],
        name: data[i][1],
        contact: data[i][2],
        services: data[i][3],
        price: data[i][4]
      });
    }
    
    // Возвращаем последние 10 записей
    var recentClients = clients.slice(-10).reverse();

    return ContentService.createTextOutput(JSON.stringify(recentClients))
                         .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({"result": "error", "error": error.toString()}))
                         .setMimeType(ContentService.MimeType.JSON);
  }
}

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