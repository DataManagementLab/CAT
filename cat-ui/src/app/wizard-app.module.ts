import {NgModule} from '@angular/core';
import {BrowserModule} from '@angular/platform-browser';
import {HTTP_INTERCEPTORS, HttpClientModule} from '@angular/common/http';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {BrowserAnimationsModule} from '@angular/platform-browser/animations';

import {MatToolbarModule} from '@angular/material/toolbar';
import {MatStepperModule} from '@angular/material/stepper';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatButtonModule} from '@angular/material/button';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatCardModule} from '@angular/material/card';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatIconModule} from '@angular/material/icon';
import {MatProgressSpinnerModule} from '@angular/material/progress-spinner';
import {MatChipsModule} from '@angular/material/chips';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatExpansionModule} from '@angular/material/expansion';
import {MatTabsModule} from '@angular/material/tabs';
import {MatCheckboxModule} from '@angular/material/checkbox';
import {MatSelectModule} from '@angular/material/select';
import {MatAutocompleteModule} from '@angular/material/autocomplete';
import {MatTreeModule} from '@angular/material/tree';
import {MatDialogModule} from '@angular/material/dialog';
import {MatBadgeModule} from '@angular/material/badge';

import {WizardRoutingModule} from './wizard-routing.module';

import {WizardParentComponent} from './wizard-parent.component';
import {ConfigurationStepperComponent} from './components/configuration/configuration-stepper.component';
import {DatabaseStepComponent} from './components/configuration/database-step/database-step.component';
import {ConfigurationStepComponent} from './components/configuration/configuration-step/configuration-step.component';
import {SimulationStepComponent} from './components/configuration/simulation-step/simulation-step.component';
import {FinishStepComponent} from './components/configuration/finish-step/finish-step.component';

import {TableComponent} from './components/table/table.component';
import {ColumnComponent} from './components/column/column.component';
import {ProcedureComponent} from './components/procedure/procedure.component';
import {ArgumentComponent} from './components/argument/argument.component';
import {UploadButtonComponent} from './components/upload-button/upload-button.component';

import {SynonymChipListComponent} from './components/synonym-chip-list/synonym-chip-list.component';
import {PairChipListComponent} from './components/pair-chip-list/pair-chip-list.component';
import {DownloadButtonComponent} from './components/download-button/download-button.component';
import {WarningDialogComponent} from './components/dialogs/warning-dialog/warning-dialog.component';
import {ViewDialogComponent} from './components/dialogs/view-dialog/view-dialog.component';
import { TemplateDialogComponent } from './components/dialogs/template-dialog/template-dialog.component';

import {NlPipe} from './components/pipes/nl.pipe';
import {JoinPipe} from './components/pipes/join.pipe';
import {MomentPipe} from './components/pipes/moment.pipe';
import {EntitySampleComponent} from './components/entity-sample/entity-sample.component';
import {JwtRefreshInterceptor} from './jwt-refresh.interceptor';
import {AuthenticationService} from './services/authentication.service';
import { HomeComponent } from './components/home/home.component';
import { TrainingStepperComponent } from './components/training/training-stepper.component';
import { BotsStepComponent } from './components/training/bots-step/bots-step.component';
import { OrderByPipe } from './components/pipes/order-by.pipe';
import { UniquePipe } from './components/pipes/unique.pipe';
import { ExtractPipe } from './components/pipes/extract.pipe';
import { FilterPipe } from './components/pipes/filter.pipe';
import { ColumnChipListComponent } from './components/column-chip-list/column-chip-list.component';
import { ColumnLookupListComponent } from './components/column-lookup-list/column-lookup-list.component';
import { TemplatingStepComponent } from './components/configuration/templating-step/templating-step.component';
import { TemplateComponent } from './components/template/template.component';
import { TemplateDisplayComponent } from './components/template-display/template-display.component';
import { TableRepresentationComponent } from './components/table-representation/table-representation.component';


@NgModule({
  declarations: [
    WizardParentComponent,
    HomeComponent,
    ConfigurationStepperComponent,
    DatabaseStepComponent,
    ConfigurationStepComponent,
    SimulationStepComponent,
    FinishStepComponent,
    TableComponent,
    ColumnComponent,
    ProcedureComponent,
    ArgumentComponent,
    SynonymChipListComponent,
    PairChipListComponent,
    UploadButtonComponent,
    DownloadButtonComponent,
    WarningDialogComponent,
    ViewDialogComponent,
    TemplateDialogComponent,
    NlPipe,
    JoinPipe,
    MomentPipe,
    EntitySampleComponent,
    TrainingStepperComponent,
    BotsStepComponent,
    OrderByPipe,
    UniquePipe,
    ExtractPipe,
    FilterPipe,
    ColumnChipListComponent,
    ColumnLookupListComponent,
    TemplatingStepComponent,
    TemplateComponent,
    TemplateDisplayComponent,
    TableRepresentationComponent
  ],
  imports: [
    WizardRoutingModule,
    BrowserModule,
    BrowserAnimationsModule,
    HttpClientModule,
    FormsModule,
    ReactiveFormsModule,
    MatToolbarModule,
    MatStepperModule,
    MatFormFieldModule,
    MatButtonModule,
    MatInputModule,
    MatListModule,
    MatProgressBarModule,
    MatCardModule,
    MatSnackBarModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatChipsModule,
    MatSidenavModule,
    MatExpansionModule,
    MatTabsModule,
    MatCheckboxModule,
    MatSelectModule,
    MatAutocompleteModule,
    MatTreeModule,
    MatDialogModule,
    MatBadgeModule
  ],
  providers: [AuthenticationService, {
    provide: HTTP_INTERCEPTORS,
    useClass: JwtRefreshInterceptor,
    multi: true
  }],
  bootstrap: [WizardParentComponent],
  entryComponents: [WarningDialogComponent, ViewDialogComponent, TemplateDialogComponent]
})
export class WizardAppModule {
}
