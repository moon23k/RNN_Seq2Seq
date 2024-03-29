import torch, evaluate



class Tester:
    def __init__(self, config, model, tokenizer, test_dataloader):
        super(Tester, self).__init__()
        
        self.model = model
        self.tokenizer = tokenizer
        self.dataloader = test_dataloader

        self.task = config.task
        self.device = config.device
        self.bos_id = config.bos_id
        self.pad_id = config.pad_id
        self.max_len = config.max_len
        self.vocab_size = config.vocab_size
        self.model_type = config.model_type
        
        self.metric_name = 'BLEU' if self.task == 'translation' else 'ROUGE'
        self.metric_module = evaluate.load(self.metric_name.lower())
        


    def test(self):
        score = 0.0         
        self.model.eval()

        with torch.no_grad():
            for batch in self.dataloader:

                x = batch['x'].to(self.device)
                y = self.tokenize(batch['y'])            
        
                pred = self.predict(x)
                pred = self.tokenize(pred)

                score += self.evaluate(pred, y)

        txt = f"TEST Result on {self.task.upper()} with {self.model_type.upper()} model"
        txt += f"\n-- Score: {round(score/len(self.dataloader), 2)}\n"
        print(txt)


    def tokenize(self, batch):
        return [self.tokenizer.decode(x) for x in batch.tolist()]


    def predict(self, x):
        batch_size = x.size(0)
        
        pred = torch.LongTensor(batch_size, self.max_len)
        pred = pred.fill_(self.pad_id).to(self.device)
        pred[:, 0] = self.bos_id

        pred_token = torch.LongTensor(batch_size).fill_(self.bos_id).to(self.device)
        hiddens = self.model.encoder(x)

        for t in range(1, self.max_len):
            out, hiddens = self.model.decoder(pred_token, hiddens)
            pred_token = out.argmax(-1)
            pred[:, t] = pred_token
        
        return pred


    def evaluate(self, pred, label):
        if all(elem == '' for elem in pred):
            return 0.0
        
        #For NMT Evaluation
        if self.task == 'translation':
            score = self.metric_module.compute(
                predictions=pred, 
                references =[[l] for l in label]
            )['bleu']
        #For Dialg & Sum Evaluation
        else:
            score = self.metric_module.compute(
                predictions=pred, 
                references =[[l] for l in label]
            )['rouge2']

        return score * 100
