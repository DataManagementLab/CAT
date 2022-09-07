export interface Templateable {
  id: string;
  name: string;
  templates: string[];
  placeholders: string[];
}

export const DEFAULT_INTENTS = [{
  id: 'greeting',
  name: 'Greet',
  templates: ['Bom dia', 'Bonjour', 'Good Morning', 'Good morning', 'Good mourning', 'Guten Morgen', 'HELLO', 'HEY', 'HEllo', 'HI', 'HI Sara', 'Hallo', 'Hei', 'Hellllooooooo', 'Hello', 'Hello Bot', 'Hello Rasa', 'Hello Sara', 'Hello sara', 'Hello!', 'Hey', 'Hey Sara', 'Hey bot', 'Heya', 'Heylo', 'Hi', 'Hi Sara', 'Hi Sara!', 'Hi bot', 'Hi man', 'Hi rasa', 'Hi sara', 'Hi sara..', 'Hi there', 'Hi!', 'Hi', 'Hi,', 'Hi, bot', 'Hieee', 'Hieeeeeeeeeeeee', 'Hola', 'I said, helllllloooooO!!!!', 'Well hello there ;)', 'What is up?', 'Whats up', 'Whats up my bot', 'Whats up?', 'ayyyy whaddup', 'bonjour', 'ey boss', 'good evening', 'good moring', 'good morning', 'greet', 'greetings', 'hai', 'hallo', 'hallo sara', 'halloo', 'halloooo', 'halo', 'halo sara', 'heeey', 'heelio', 'hell9o', 'hellio', 'hello', 'hello Sara', 'hello everybody', 'hello friend', 'hello hi', 'hello is anybody there', 'hello it is me again', 'hello robot', 'hello sara', 'hello sweatheart', 'hello sweet boy', 'hello there', 'hello world', 'hello, my name is Charles Pfeffer', 'hello?', 'hello]', 'hellooo', 'helloooo', 'helo', 'hey', 'hey bot', 'hey bot!', 'hey dude', 'hey hey', 'hey lets talk', 'hey rasa', 'hey sara', 'hey ther', 'hey there', 'hey there boy', 'hey there..', 'hey, lets talk', 'hey, sara!', 'heya', 'heyho', 'heyo', 'hhola', 'hi', 'hi !', 'hi Mister', 'hi again', 'hi can you speak ?', 'hi folks', 'hi friend', 'hi friends', 'hi hi', 'hi im Sandra Hernandez', 'hi im Amanda Anderson', 'hi mrs rasa', 'hi pal!', 'hi sara', 'hi there', 'hi there its me', 'hi!', 'hi.........................................................', 'hi?', 'hieee', 'hii', 'hiihihi', 'hiii', 'hlo', 'hola', 'howdy', 'i am Karen Mease', 'jojojo', 'jop', 'konichiwa', 'merhaba', 'ola sara', 'rasa hello', 'salut', 'sup', 'wasssup', 'wasssup!', 'what up', 'whats popping', 'whats up', 'yo', 'yoo'],
  placeholders: []
}, {
  id: 'goodbye',
  name: 'Bye',
  templates: ['Bye', 'Bye bye', 'adios', 'adios?', 'bye', 'bye .', 'bye :P', 'bye bot', 'bye bye', 'bye bye bot', 'bye for now', 'bye udo', 'bye was nice talking to you', 'bye!', 'byee', 'catch you later', 'ciao', 'cya', 'farewell', 'good bye', 'good bye rasa bot!', 'good night', 'goodbye', 'goodbye.', 'goodnight', 'gotta go', 'k byyye #slay', 'ok Bye', 'ok bye', 'ok, bye', 'ok.bye', 'see u later', 'see ya', 'see you', 'see you . bye', 'take care', 'then bye', 'tlak to you later', 'toodle-oo'],
  placeholders: []
}, {
  id: 'affirm',
  name: 'Affirm',
  templates: ['Accept', 'Awesome!', 'Cool', 'Good', 'Great', 'I accept', 'I accept.', 'I agree', 'I am using it', 'I changed my mind. I want to accept it', 'I do', 'I get it', 'I guess so', 'I have used it in the past', 'I will', 'Id absolutely love that', 'Im sure I will!', 'Im using it', 'Nice', 'OK', 'Ofcourse', 'Oh yes', 'Oh, ok', 'Ok', 'Ok lets start', 'Ok.', 'Okay', 'Okay!', 'PLEASE', 'SURE', 'Sure', 'Sweet', 'That would be great', 'YES', 'YUP', 'Yea', 'Yeah', 'Yeah sure', 'Yep', 'Yep thats fine', 'Yep!', 'Yepp', 'Yes', 'Yes I do', 'Yes please', 'Yes please!', 'Yes, I accept', 'Yes.', 'Yup', 'a little', 'absolutely', 'accept', 'accepted', 'agreed', 'ah ok', 'alright', 'alright, cool', 'amayzing', 'amazing!', 'awesome', 'awesome!', 'confirm', 'cool', 'cool :)', 'cool story bro', 'cool!', 'coolio', 'definitely yes without a doubt', 'done', 'fair enough', 'fcourse', 'fine', 'fuck yeah!', 'go', 'go ahead', 'go for it', 'going super well', 'good', 'good.', 'great', 'great lets do that', 'great!', 'hell yeah', 'hell yes', 'hm, id like that', 'how nice!', 'i accept', 'i agree', 'i am!', 'i want that', 'i will!', 'it is ok', 'its okay', 'ja', 'ja cool', 'ja thats great', 'jezz', 'jo', 'k', 'kk', 'lets do it', 'lets do this', 'nice', 'not bad', 'of course', 'ofcoure i do', 'ofcourse', 'oh awesome!', 'oh cool', 'oh good !!', 'oh super', 'ok', 'ok cool', 'ok fine', 'ok friend', 'ok good', 'ok great', 'ok i accept', 'ok sara', 'ok, I behave now', 'ok, I understood', 'ok, Sara', 'ok...', 'okay', 'okay cool', 'okay sure', 'okay..', 'oki doki', 'okie', 'ook', 'oui', 'perfect', 'please', 'si', 'sort of', 'sure', 'sure thing', 'sure!', 'that is cool', 'that ok', 'that sounds fine', 'thats great', 'thats fine', 'thats good', 'thats great', 'top', 'uh-huh', 'very much', 'well yes', 'y', 'ya', 'ya cool', 'ya go for it', 'ya i want', 'ya please', 'ya thats cool', 'yaah', 'yap', 'yaps', 'yas', 'yay', 'ye', 'ye splease', 'yea', 'yeah', 'yeah do that', 'yeah sure', 'yeah=', 'yeah, why not', 'yeeeeezzzzz', 'yeeees', 'yep', 'yep i want that', 'yep if i have to', 'yep please', 'yep thats nice', 'yep thats cool', 'yep, will do thank you', 'yep. :/', 'yes', 'yes ...', 'yes I do', 'yes accept please', 'yes baby', 'yes cool', 'yes give me information', 'yes go ahead', 'yes go for it', 'yes great', 'yes i accept', 'yes i agree', 'yes i have built a bot before', 'yes i have!', 'yes it is', 'yes it was okay', 'yes of course', 'yes pleae', 'yes please', 'yes please!', 'yes pls', 'yes sirfr', 'yes thats great', 'yes thats what i want', 'yes you can', 'yes', 'yes, Id love to', 'yes, cool', 'yes, give me information, please', 'yes,i am', 'yes.', 'yesh', 'yess', 'yessoo', 'yesss', 'yesssss', 'yesyestyes', 'yesyesyes', 'yez', 'yop', 'you asked me a yes or no question, which i answered with yes', 'you got me, I accept, if you want me to', 'yres', 'ys', 'yup', 'yyeeeh'],
  placeholders: []
}, {
  id: 'deny',
  name: 'Deny',
  templates: ['I dont want to', 'I dont want to give it to you', 'I dont want to say', 'I dont want to tell', 'Im not giving you my email address', 'Im not going to give it to you', 'NEIN', 'NO', 'NO DON"T WANT THIS!', 'Nah', 'Neither', 'Never', 'Nevermind', 'No', 'No thank you', 'No, not really.', 'No, thank you', 'No.', 'Nopes', 'Not really', 'absolutely not', 'decline', 'definitely not', 'deny', 'i decline', 'i don not like this', 'i dont think so', 'i dont want either of those', 'i dont want to', 'i dont want to give you my email', 'i dont want to', 'i dont want to accept :P lol', 'i guess it means - no', 'im afraid not', 'im not sure', 'it is going pretty badly', 'it sucks', 'it sux', 'n', 'na', 'nah', 'nah Im good', 'nah not for me', 'nah, first time', 'nah, im good', 'nehi', 'nein', 'neither', 'never', 'never mind', 'no', 'no :(', 'no I dont want', 'no I havent decided yet if I want to sign up', 'no and no again', 'no bots at all', 'no go', 'no i cant', 'no i dont accept', 'no i dont want to', 'no i dont want to accept :P lol', 'no i wont', 'no maam', 'no sir', 'no sorry', 'no thank s', 'no thank you', 'no thanks', 'no way', 'no you did it wrong', 'no!!!!', 'no, i hate it', 'no, my frst time', 'no, thank you', 'no, thanks', 'no, thankyou', 'no. u r idiot', 'non', 'noooooooooo', 'noooooooooooooooooooooooooooooooooooooooo', 'nop', 'nope', 'nope!', 'nope. i am good', 'not going well at all', 'not really', 'not right now', 'not yet', 'nö', 'sorry not right now', 'still dont want to tell', 'thanks but no thanks', 'this sucks', 'very bad', 'I do not need help installing', 'I dont wanna tell the name of my company', 'no stop', 'stop it, i do not care!!!'],
  placeholders: []
}, {
  id: 'ask_more_options',
  name: 'Ask More Options',
  templates: ['Can you show me more options?', 'Show me more', 'What are other options', 'Can is see more?', 'sohw me more', 'i wanna see more', 'i need to see more :/', 'what else do you have?'],
  placeholders: []
}, {
  id: 'ask_previous_options',
  name: 'Ask Previous Options',
  templates: ['Can you scroll back?', 'Can you go back?', 'Can you show me the previous options?', 'it was one of the before', 'show me the ones before that', 'Go back'],
  placeholders: []
}, {
  id: 'select_option',
  name: 'Select option',
  templates: ['Ill go for option {choice}', 'I want option {choice}', 'I take the {choice} option', 'Ill take the {choice} one'],
  placeholders: ['choice']
}, {
  id: 'dont_care',
  name: 'Dont Care',
  templates: ['I dont know', 'Dontt know', 'I dont care', 'Dont care', 'No i dont know', 'I dont give a ...'],
  placeholders: []
}, {
  id: 'done',
  name: 'Done',
  templates: ['Cool. Thanks', 'Great, thanks', 'Thank you', 'Thank you Sara', 'Thank you so much', 'Thanks!', 'Thanks', 'Thanks bot', 'Thanks for that', 'Thanks!', 'amazing, thanks', 'cheers', 'cheers bro', 'cool thank you', 'cool thanks', 'cool, thanks', 'danke', 'great thanks', 'ok thanks', 'ok thanks sara', 'ok thanks!', 'perfect thank you', 'thank u', 'thank you', 'thank you anyways', 'thanks', 'thanks a bunch for everything', 'thanks a lot', 'thanks for forum link, Ill check it out', 'thanks for the help', 'thanks this is great news', 'thanks you', 'thanks!', 'thankyou', 'thnks', 'thx', 'yes thanks'],
  placeholders: []
}, {
  id: 'give_up',
  name: 'Give Up',
  templates: ['Thats not what I wanted', 'You cant help me'],
  placeholders: []
}, {
  id: 'ask_options',
  name: 'Ask Options',
  templates: ['Can you show me the results', 'What are my options', 'what aer otpions', 'I need to see the options'],
  placeholders: []
}] as Templateable[];

export const BEGIN_TRANSACTION_TEMPLATE = {
  id: 'begin_',
  name: 'Begin Transaction ',
  templates: ['I want to {predicate} {argument}', 'Can you {predicate} {argument}?'],
  placeholders: ['predicate', 'argument']
};

export const INFORM_SELECTION_TEMPLATE = {
  id: 'inform_form_',
  name: 'Inform Selection Values ',
  templates: ['The {table_nl} {column_nl} is {value}'],
  placeholders: []
};

export const INFORM_CHOICE_TEMPLATE = {
  id: 'inform_',
  name: 'Inform ',
  templates: ['Set {slot_name} to {choice}', 'The {slot_name} is {choice}'],
  placeholders: ['slot_name', 'choice']
};

export const INFORM_TRUE_BOOL_CHOICE_TEMPLATE = {
  id: 'inform_bool_',
  name: 'Inform Positive ',
  templates: ['Yes i want {slot_name}'],
  placeholders: ['slot_name']
};

export const INFORM_FALSE_BOOL_CHOICE_TEMPLATE = {
  id: 'inform_bool_',
  name: 'Inform Negative',
  templates: ['No I do not want {slot_name}'],
  placeholders: ['slot_name']
};

export const DEFAULT_RESPONSES = [
  {
    id: 'utter_ask_howcanhelp',
    name: 'Greet',
    templates: ['Hey, how can i help you?', 'What can I do for you?'],
    placeholders: []
  }, {
    id: 'utter_bye',
    name: 'Bye',
    templates: ['Goodbye', 'Bye'],
    placeholders: []
  }, {
    id: 'utter_ask_rephrase',
    name: 'Ask Rephrase',
    templates: ['Can you rephrase that?', 'Sorry i didnt get that can you repeat that?'],
    placeholders: []
  }] as Templateable[];

export const ASK_PARAMETER_TEMPLATE = {
  id: 'utter_ask_parameter_',
  name: 'Ask Parameter ',
  templates: ['Okay therefor i need the {param_nl}'],
  placeholders: ['param_nl']
}

export const ASK_SELECT_TEMPLATE = {
  id: 'utter_ask_',
  name: 'Ask Selection ',
  templates: ['Can you please tell me the {table_nl}s {column_nl}', 'Alright can you provide me the {table_nl}s {column_nl}'],
  placeholders: ['table_nl', 'column_nl', 'table', 'column']
};

export const ASK_CHOICE_TEMPLATE = {
  id: 'utter_ask_choice_',
  name: 'Ask Choice ',
  templates: ['Can you please tell me the {slot_nl}?', 'Alright, can you provide me the {slot_nl}?'],
  placeholders: ['slot_nl']
};

export const PROPOSE_TASK_TEMPLATE = {
  id: 'utter_propose_begin_transaction_',
  name: 'Propose Task ',
  templates: ['So you want to {predicate} {argument}?'],
  placeholders: ['predicate', 'argument']
};

export const PROPOSE_SELECTION_TEMPLATE = {
  id: 'utter_propose_',
  name: 'Propose Selection ',
  templates: ['Is this the {table_nl} you were looking for?'],
  placeholders: []
};

export const PROPOSE_CHOICE_TEMPLATE = {
  id: 'utter_propose_choice',
  name: 'Propose Choice ',
  templates: ['Is {choice} the correct {slot_nl}?'],
  placeholders: ['slot_nl', 'choice']
};

export const PROPOSE_TRANSACTION_TEMPLATE = {
  id: 'utter_propose_transaction',
  name: 'Propose Transaction ',
  templates: ['Alright I am gonna {predicate} {argument} with the following information'],
  placeholders: ['predicate', 'argument']
};

export const SUCCESS_TRANSACTION_TEMPLATE = {
  id: 'utter_success_transaction_',
  name: 'Successful Transaction ',
  templates: ['Successfully {predicate} {argument}'],
  placeholders: ['predicate', 'argument']
}

export const FAILED_TRANSACTION_TEMPLATE = {
  id: 'utter_failed_transaction_',
  name: 'Failed Transaction ',
  templates: ['Sorry i could not {predicate} {argument}: {transaction_error}'],
  placeholders: ['predicate', 'argument', 'transaction_error']
}
