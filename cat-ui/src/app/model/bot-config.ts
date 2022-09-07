import {DialogPolicy} from './dialog-policy';

type Language = 'en' | 'de' | undefined;

export interface BotPipeline {
  name: string;
}

export interface BotConfig {
  language: Language;
  pipeline: BotPipeline[];
  policies: DialogPolicy[];
}
