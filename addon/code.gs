function buildAddOn(e) {
  var card = CardService.newCardBuilder();
  card.setHeader(CardService.newCardHeader()
    .setTitle('📋 Create Teamwork Task'));

  // Email context section
  var emailContext = getEmailContextFromEvent(e);
  var contextSection = CardService.newCardSection()
    .addWidget(CardService.newTextParagraph()
      .setText('<b>From:</b> ' + emailContext.sender + '<br><b>Subject:</b> ' + emailContext.subject));

  // Command input section
  var inputSection = CardService.newCardSection()
    .addWidget(CardService.newTextInput()
      .setFieldName('command')
      .setTitle('💬 Natural Language Command')
      .setHint("e.g., 'Create urgent task: review contract, due Friday'")
      .setMultiline(true))
    .addWidget(CardService.newTextButton()
      .setText('Create Task')
      .setOnClickAction(CardService.newAction()
        .setFunctionName('createTaskFromCard')));

  card.addSection(contextSection);
  card.addSection(inputSection);

  return card.build();
}

function createTaskFromCard(e) {
  var command = e.formInput.command;

  if (!command) {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('⚠️ Please enter a command'))
      .build();
  }

  var emailContext = getEmailContextFromEvent(e);
  var result = sendToBackend(command, emailContext);

  if (result.success) {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('✅ Task created: ' + result.task_title))
      .build();
  } else {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('❌ Error: ' + result.error))
      .build();
  }
}

function getEmailContextFromEvent(e) {
  try {
    // Get message ID from event object
    var messageId = e.gmail.messageId;
    var accessToken = e.gmail.accessToken;

    // Use Gmail API to get message details
    var message = GmailApp.getMessageById(messageId);

    return {
      subject: message.getSubject(),
      sender: message.getFrom(),
      body: message.getPlainBody().substring(0, 500),
      date: message.getDate().toISOString(),
      to: message.getTo()
    };
  } catch (error) {
    Logger.log('Error getting email context: ' + error.message);

    // Fallback to active conversation
    try {
      var message = GmailApp.getActiveConversation().getMessages()[0];
      return {
        subject: message.getSubject(),
        sender: message.getFrom(),
        body: message.getPlainBody().substring(0, 500),
        date: message.getDate().toISOString(),
        to: message.getTo()
      };
    } catch (fallbackError) {
      return {
        subject: '(no email selected)',
        sender: 'N/A',
        body: '',
        date: new Date().toISOString(),
        to: ''
      };
    }
  }
}

function sendToBackend(command, emailContext) {
  var url = 'https://gmail-to-teamwork-740248311644.us-central1.run.app/create-task';
  var payload = {
    command: command,
    email: emailContext
  };

  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    var data = JSON.parse(response.getContentText());
    return data;
  } catch (error) {
    return {
      success: false,
      error: 'Connection failed: ' + error.message
    };
  }
}

function getEmailContext() {
  try {
    var message = GmailApp.getActiveConversation().getMessages()[0];
    return {
      subject: message.getSubject(),
      sender: message.getFrom(),
      body: message.getPlainBody().substring(0, 500),
      date: message.getDate().toISOString(),
      to: message.getTo()
    };
  } catch (error) {
    return {
      subject: '(no email selected)',
      sender: 'N/A',
      body: '',
      date: new Date().toISOString(),
      to: ''
    };
  }
}
