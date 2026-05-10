function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('sidebar')
    .setWidth(400)
    .setHeight(600)
    .setSandboxMode(HtmlService.SandboxMode.IFRAME);
}

function onGmailMessage(e) {
  const accessToken = e.gmail.accessToken;
  GmailApp.setCurrentMessageAccessToken(accessToken);

  const threadId = e.gmail.threadId;
  const threads = GmailApp.getThreadById(threadId);
  const messages = threads.getMessages();
  const message = messages[0];

  const section = CardService.newCardSection()
    .addWidget(CardService.newTextParagraph()
      .setText('<b>From:</b> ' + message.getFrom()))
    .addWidget(CardService.newTextParagraph()
      .setText('<b>Subject:</b> ' + message.getSubject()))
    .addWidget(CardService.newTextInput()
      .setFieldName('command')
      .setTitle('💬 Natural Language Command')
      .setMultiline(true)
      .setHint('e.g., "Create urgent task: review"'))
    .addWidget(CardService.newButtonSet()
      .addButton(CardService.newTextButton()
        .setText('Create Task')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('handleCreateTask')
          .setParameters({
            'threadId': threadId
          }))));

  const card = CardService.newCardBuilder()
    .setHeader(CardService.newCardHeader()
      .setTitle('📋 Create Teamwork Task'))
    .addSection(section)
    .build();

  return [card];
}

function handleCreateTask(e) {
  const command = e.formInput.command;
  const threadId = e.parameters.threadId;

  if (!command || command.trim() === '') {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('Please enter a command'))
      .build();
  }

  try {
    const threads = GmailApp.getThreadById(threadId);
    const messages = threads.getMessages();
    const message = messages[0];

    const emailContext = {
      subject: message.getSubject(),
      sender: message.getFrom(),
      body: message.getPlainBody().substring(0, 500),
      date: message.getDate().toISOString(),
      to: message.getTo()
    };

    const backendUrl = 'https://gmail-to-teamwork-740248311644.us-central1.run.app/create-task';
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        command: command,
        email: emailContext
      }),
      muteHttpExceptions: true
    };

    const response = UrlFetchApp.fetch(backendUrl, options);
    const result = JSON.parse(response.getContentText());

    if (result.success) {
      return CardService.newActionResponseBuilder()
        .setNotification(CardService.newNotification()
          .setText('✅ Task created: ' + result.task_title))
        .setOpenLink(CardService.newOpenLink()
          .setUrl(result.task_url))
        .build();
    } else {
      return CardService.newActionResponseBuilder()
        .setNotification(CardService.newNotification()
          .setText('❌ Error: ' + result.error))
        .build();
    }

  } catch (error) {
    Logger.log('Error: ' + error);
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('❌ Connection failed. Is backend running?'))
      .build();
  }
}



