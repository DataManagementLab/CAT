export interface DialogPolicy {
  name: string;
  priority: number;
}

type PosEncoding = 'timing' | 'emb' | undefined;
type BatchStrategy = 'balanced' | 'sequenced' | undefined;
type SimilarityType = 'auto' | 'cosine' | 'inner' | undefined;
type LossType = 'softmax' | 'margin' | undefined;

export interface EmbeddingPolicy extends DialogPolicy {
  /* nn architecture
   a list of hidden layers sizes before user embed layer
   number of hidden layers is equal to the length of this list */
  hiddenLayersSizesPreDial: number[];
  /* a list of hidden layers sizes before bot embed layer
     number of hidden layers is equal to the length of this list */
  hiddenLayersSizesBot: number[];
  /* number of units in transformer */
  transformerSize: number;
  /* number of transformer layers */
  numTransformerLayers: number;
  /* type of positional encoding in transformer */
  posEncoding: PosEncoding;
  /* max sequence length if pos_encoding='emb' */
  maxSeqLength: number;
  /* number of attention heads in transformer */
  numHeads: number;
  /* training parameters */
  /*  initial and final batch sizes:
    batch size will be linearly increased for each epoch */
  batchSize: number[];
  /* how to create batches */
  batchStrategy: BatchStrategy;
  /* number of epochs */
  epochs: number;
  /* set random seed to any int to get reproducible results */
  randomSeed: number;
  /* embedding parameters */
  /* dimension size of embedding vectors */
  embedDim: number;
  /* the type of the similarity */
  numNeg: number;
  /* flag if minimize only maximum similarity over incorrect labels */
  similarityType: SimilarityType;
  /* the type of the loss function */
  lossType: LossType;
  /* how similar the algorithm should try to make embedding vectors for correct labels
     should be 0.0 < ... < 1.0 for 'cosine' */
  muPos: number;
  /* maximum negative similarity for incorrect labels
     should be -1.0 < ... < 1.0 for 'cosine' */
  muNeg: number;
  /* the number of incorrect labels, the algorithm will minimize
     their similarity to the user input during training */
  useMaxSimNeg: boolean;
  /* flag which loss function to use
     scale loss inverse proportionally to confidence of correct prediction */
  scaleLoss: boolean;
  /* regularization */
  /* the scale of L2 regularization */
  c2: number;
  /* the scale of how important is to minimize the maximum similarity between embeddings of different labels*/
  cEmb: number;
  /* dropout rate for dial nn */
  dropoutRateA: number;
  /* dropout rate for bot nn */
  dropoutRateB: number;
  /* visualization of accuracy*/
  /* how often calculate validation accuracy
     small values may hurt performance */
  evaluateEveryNumEpochs: number;
  /* how many examples to use for hold out validation set
    large values may hurt performance*/
  evaluateOnNumExamples: number;

  /*constructor() {
    super('EmbeddingPolicy', 1);
    this.hiddenLayersSizesPreDial = [];
    this.hiddenLayersSizesBot = [];
    this.transformerSize = 128;
    this.numTransformerLayers = 1;
    this.posEncoding = 'timing';
    this.maxSeqLength = 256;
    this.numHeads = 4;
    this.batchSize = [8, 32];
    this.batchStrategy = 'balanced';
    this.epochs = 1;
    this.randomSeed = null;
    this.embedDim = 20;
    this.numNeg = 20;
    this.similarityType = 'auto';
    this.lossType = 'softmax';
    this.muPos = 0.8;
    this.muNeg = -0.2;
    this.useMaxSimNeg = true;
    this.scaleLoss = true;
    this.c2 = 0.001;
    this.cEmb = 0.8;
    this.dropoutRateA = 0.1;
    this.dropoutRateB = 0.0;
    this.evaluateEveryNumEpochs = 20;
    this.evaluateOnNumExamples = 0;
  }*/
}

export interface KerasPolicy extends DialogPolicy {
  rnnSize: number;
  epochs: number;
  batchSize: number;
  validationSplit: number;
  randomSeed: number;

  /*constructor() {
    super('KerasPolicy', 1);
    this.rnnSize = 32;
    this.epochs = 100;
    this.batchSize = 32;
    this.validationSplit = 0.1;
    this.randomSeed = null;
  }*/
}

export interface IntentMapping {
  intentName: string;
  triggers: string;
}

export interface MappingPolicy extends DialogPolicy {
  mappings: IntentMapping;
  /*constructor() {
    super('MappingPolicy', 2);
  }*/
}
