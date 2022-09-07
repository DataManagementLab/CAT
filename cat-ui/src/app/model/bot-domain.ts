type SlotType = 'text' | 'unfeaturized' | undefined;

export interface BotDomain {
  actions: string[];
  entities: string[];
  intents: BotIntent[];
  slots: BotSlot[];
  templates: ActionTemplate[];
}

export interface BotSlot {
  name: string;
  type: SlotType;
}

export interface BotIntent {
  name: string;
  triggers: string[];
}

export interface ActionTemplate {
  actionName: string;
  templates: Template[];
}

export interface Template {
  text: string;
}
