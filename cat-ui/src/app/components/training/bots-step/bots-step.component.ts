import {Component, Input, OnInit} from '@angular/core';
import {BotService} from '../../../services/bot.service';
import {Bot} from '../../../model/bot';
import {BotConfig} from '../../../model/bot-config';
import {AuthenticationService} from '../../../services/authentication.service';
import {MomentPipe} from '../../pipes/moment.pipe';
import {UniquePipe} from '../../pipes/unique.pipe';
import {Moment} from 'moment';
import {BotDomain} from '../../../model/bot-domain';
import {ViewDialogComponent} from '../../dialogs/view-dialog/view-dialog.component';
import {MatDialog} from '@angular/material';
import {DialogPolicy, KerasPolicy} from '../../../model/dialog-policy';

@Component({
  selector: 'app-bots-step',
  templateUrl: './bots-step.component.html',
  styleUrls: ['./bots-step.component.css'],
  providers: [MomentPipe, UniquePipe]
})
export class BotsStepComponent implements OnInit {

  optionGroups: Moment[];
  bots: Bot[];
  selectedBot: Bot;
  stories: string[] = [];
  botDomain: BotDomain;
  botConfig: BotConfig;

  constructor(private authService: AuthenticationService, private botService: BotService,
              private dialog: MatDialog,
              private momentPipe: MomentPipe, private uniquePipe: UniquePipe) {
  }

  ngOnInit() {
    this.authService.authenticatedChange.subscribe(isAuthenticated => {
      if (isAuthenticated) {
        this.botService.getBots()
          .subscribe(bots => {
            this.bots = bots;
            const timestamps = bots.map<Moment>((b: Bot) => {
              return this.momentPipe.transform(b.created, true);
            });
            this.optionGroups = timestamps.filter((v, i) => {
              return timestamps.map(t => t.valueOf()).indexOf(v.valueOf()) === i;
            });
          });
      } else {
        this.bots = [];
        this.optionGroups = [];
      }
    });
  }

  filterCreatedDate(bots: Bot[], date: Moment): Bot[] {
    return bots.filter((b) => {
      return this.momentPipe.transform(b.created, true).valueOf() === date.valueOf();
    }).sort((a, b) => {
      if (a.created < b.created) {
        return 1;
      } else {
        return -1;
      }
    });
  }

  showStories() {
    this.dialog.open(ViewDialogComponent, {
      width: '800px',
      data: {
        title: 'Stories',
        data: this.stories.join('\n\n')
      }
    });

  }

  onBotChange(event) {
    this.botService.getStories(this.selectedBot.path)
      .subscribe(stories => {
        this.stories = stories;
      });

    this.botService.getBotDomain(this.selectedBot.path)
      .subscribe(domain => {
        this.botDomain = domain;
      });

    this.botService.getBotConfig(this.selectedBot.path)
      .subscribe(config => {
        this.botConfig = config;
      });
  }

}
