function buildAddOn(e) {
  var card = CardService.newCardBuilder();
  card.setHeader(CardService.newCardHeader()
    .setTitle('📋 Create Teamwork Task'));

  // Email context section
  var emailContext = getEmailContextFromEvent(e);

  var emailSummary = emailContext.subject !== '(no email selected)'
    ? '<b>From:</b> ' + emailContext.sender + '<br><b>Subject:</b> ' + emailContext.subject
    : '<i>No email selected</i>';

  var contextSection = CardService.newCardSection()
    .addWidget(CardService.newTextParagraph()
      .setText(emailSummary));

  // Input section for client name
  var inputSection = CardService.newCardSection()
    .addWidget(CardService.newTextInput()
      .setFieldName('client_name')
      .setTitle('🏢 Client/Company Name')
      .setHint('Enter client or company name'))
    .addWidget(CardService.newTextButton()
      .setText('Analyze Issue')
      .setOnClickAction(CardService.newAction()
        .setFunctionName('analyzeEmailIssue')));

  card.addSection(contextSection);
  card.addSection(inputSection);

  return card.build();
}

function analyzeEmailIssue(e) {
  var clientName = e.formInput.client_name;

  if (!clientName) {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('⚠️ Please enter client/company name'))
      .build();
  }

  var emailContext = getEmailContextFromEvent(e);
  var result = analyzeEmail(emailContext, clientName);

  if (result.success) {
    // Build new card showing summary
    var card = CardService.newCardBuilder();
    card.setHeader(CardService.newCardHeader()
      .setTitle('📋 Review & Create Task'));

    // Project confirmation section (prominent)
    var projectWidget = CardService.newDecoratedText()
      .setTopLabel('✅ Project Found')
      .setText('<b>' + result.project.name + '</b>');

    // Only show company if it exists
    if (result.project.company && result.project.company !== 'N/A') {
      projectWidget.setBottomLabel('Company: ' + result.project.company);
    }

    var projectSection = CardService.newCardSection()
      .addWidget(projectWidget);

    // Issue summary section
    var summarySection = CardService.newCardSection()
      .setHeader('Issue Summary')
      .addWidget(CardService.newTextParagraph()
        .setText(result.summary));

    var confirmSection = CardService.newCardSection()
      .addWidget(CardService.newTextInput()
        .setFieldName('task_title')
        .setTitle('Task Title (optional)')
        .setHint('Leave blank to auto-generate from summary')
        .setValue(''))
      .addWidget(CardService.newTextButton()
        .setText('✅ Create Task')
        .setOnClickAction(CardService.newAction()
          .setFunctionName('createTaskWithSummary')
          .setParameters({
            'client_name': clientName,
            'project_id': String(result.project.id),
            'project_name': result.project.name,
            'summary': result.summary
          })));

    card.addSection(projectSection);
    card.addSection(summarySection);
    card.addSection(confirmSection);

    return CardService.newActionResponseBuilder()
      .setNavigation(CardService.newNavigation().pushCard(card.build()))
      .build();
  } else {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('❌ ' + result.error))
      .build();
  }
}

function createTaskWithSummary(e) {
  var clientName = e.parameters.client_name;
  var projectId = e.parameters.project_id;
  var projectName = e.parameters.project_name;
  var summary = e.parameters.summary;
  var customTitle = e.formInput.task_title || '';

  var command = customTitle || summary;
  var emailContext = getEmailContextFromEvent(e);

  var result = sendToBackend(command, emailContext, clientName, projectId, projectName);

  if (result.success) {
    return CardService.newActionResponseBuilder()
      .setNotification(CardService.newNotification()
        .setText('✅ Task created in ' + result.project_name))
      .setNavigation(CardService.newNavigation().popToRoot())
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

function analyzeEmail(emailContext, clientName) {
  var url = 'https://gmail-to-teamwork-740248311644.us-central1.run.app/analyze-email';
  var payload = {
    email: emailContext,
    client_name: clientName
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

function sendToBackend(command, emailContext, clientName, projectId, projectName) {
  var url = 'https://gmail-to-teamwork-740248311644.us-central1.run.app/create-task';
  var payload = {
    command: command,
    email: emailContext,
    client_name: clientName,
    project_id: projectId,
    project_name: projectName
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
