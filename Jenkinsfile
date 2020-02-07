pipeline {
  agent any
  environment {
      PATH="/home/mrjenkins/anaconda3/envs/py37p1.4.0/bin:$PATH"
  }
  options {
    timeout(time: 1, unit: 'HOURS')
    disableConcurrentBuilds()
   }
  stages {

    stage('PyTorch version') {
      steps {
        sh 'python -c "import torch; print(torch.__version__)"'
      }
    }
    stage('Install test requirements') {
      steps {
        sh 'pip install -r requirements/requirements_test.txt'
      }
    }
    stage('Code formatting checks') {
      steps {
        sh 'python setup.py style'
      }
    }


    stage('Squad') {
      failFast true
      parallel {       
        stage('Squad v1.1') {
          steps {
            sh './reinstall.sh && cd examples/nlp/question_answering && DATA_DIR=/home/mrjenkins/TestData/nlp/squad_mini/v1.1/ CUDA_VISIBLE_DEVICES=0 python question_answering_squad.py --amp_opt_level O1 --train_file $DATA_DIR/train-v1.1.json --dev_file $DATA_DIR/dev-v1.1.json --work_dir outputs/squadfv1 --batch_size 8 --save_step_freq 300 --num_epochs 3 --lr_policy WarmupAnnealing  --lr 3e-5 --do_lower_case'
            sh 'cd examples/nlp/question_answering && FSCORE=$(cat outputs/squadv1/log_globalrank-0_localrank-0.txt |  grep "f1" |tail -n 1 |egrep -o "[0-9.]+"|tail -n 1 ) && echo $FSCORE && if [ $(echo "$FSCORE < 50.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
            sh 'DATA_DIR=/home/mrjenkins/TestData/nlp/squad_mini/v1.1/  rm -rf examples/nlp/question_answering/outputs/squadv1 && rm -rf $DATA_DIR/*cache*'
          }
        }
        stage('Squad v2.0') {
          steps {
            sh 'cd examples/nlp/question_answering && DATA_DIR=/home/mrjenkins/TestData/nlp/squad_mini/v2.0/ CUDA_VISIBLE_DEVICES=1 python question_answering_squad.py --amp_opt_level O1 --train_file $DATA_DIR/train-v2.0.json --dev_file $DATA_DIR/dev-v2.0.json --work_dir outputs/squadv2 --batch_size 8 --save_step_freq 300 --num_epochs 3 --lr_policy WarmupAnnealing  --lr 3e-5 --do_lower_case --version_2_with_negative'
            sh 'cd examples/nlp/question_answering && FSCORE=$(cat outputs/squadv2/log_globalrank-0_localrank-0.txt |  grep "f1" |tail -n 1 |egrep -o "[0-9.]+"|tail -n 1 ) && echo $FSCORE && if [ $(echo "$FSCORE < 50.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
            sh 'DATA_DIR=/home/mrjenkins/TestData/nlp/squad_mini/v2.0/  rm -rf examples/nlp/question_answering/outputs/squadv2 && rm -rf $DATA_DIR/*cache*'
          }
        }
      }
    }

    // stage('BERT pretraining') {
    //   failFast true
    //   parallel {       
    //     stage('BERT offline preprocessing') {
    //       steps {
    //         sh './reinstall.sh && cd examples/nlp/language_modeling && CUDA_VISIBLE_DEVICES=0 python bert_pretraining.py --amp_opt_level "O1" --data_dir /home/mrjenkins/TestData/nlp/wiki_book_mini  --work_dir outputs/bert_lm --batch_size 8 --config_file /home/mrjenkins/TestData/nlp/bert_configs/uncased_L-12_H-768_A-12.json  --save_step_freq 200 --max_steps 300  --num_gpus 1  --batches_per_step 1 --lr_policy SquareRootAnnealing --beta2 0.999 --beta1 0.9  --lr_warmup_proportion 0.01 --optimizer adam_w  --weight_decay 0.01  --lr 0.875e-4 --preprocessed_data '
    //         sh 'cd examples/nlp/language_modeling && LOSS=$(cat outputs/bert_lm/log_globalrank-0_localrank-0.txt |  grep "Loss" |tail -n 1| awk "{print $7}" | egrep -o "[0-9.]+" ) && echo $LOSS && if [ $(echo "$LOSS > 11.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
    //         sh 'rm -rf examples/nlp/language_modeling/outputs'
    //       }
    //     }
    //   }
    // }

    //     stage('BERT pretraining') {
    //   failFast true
    //   parallel { 
    //     stage('BERT on the fly preprocessing') {
    //       steps {
    //         sh './reinstall.sh && cd examples/nlp/language_modeling && CUDA_VISIBLE_DEVICES=0 python bert_pretraining.py --amp_opt_level "O1" --data_dir /home/mrjenkins/TestData/nlp/wikitext-2 --dataset_name wikitext-2 --work_dir outputs/bert_lm --batch_size 64 --lr 0.01 --lr_policy CosineAnnealing --lr_warmup_proportion 0.05 --tokenizer sentence-piece --vocab_size 3200 --hidden_size 768 --intermediate_size 3072 --num_hidden_layers 6 --num_attention_heads 12 --hidden_act "gelu" --save_step_freq 200 --sample_size 10000000 --mask_probability 0.15 --short_seq_prob 0.1 --max_steps=300'
    //         sh 'cd examples/nlp/language_modeling && LOSS=$(cat outputs/bert_lm/log_globalrank-0_localrank-0.txt |   grep "Loss" |tail -n 1| awk "{print $7}" | egrep -o "[0-9.]+" ) && echo $LOSS && if [ $(echo "$LOSS > 8.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
    //         sh 'rm -rf examples/nlp/language_modeling/outputs'
    //       }
    //     }        
    //     stage('BERT offline preprocessing') {
    //       steps {
    //         sh './reinstall.sh && cd examples/nlp/language_modeling && CUDA_VISIBLE_DEVICES=0 python bert_pretraining.py --amp_opt_level "O1" --data_dir /home/mrjenkins/TestData/nlp/wikitext-2 --dataset_name wikitext-2 --work_dir outputs/bert_lm --batch_size 64 --lr 0.01 --lr_policy CosineAnnealing --lr_warmup_proportion 0.05 --tokenizer sentence-piece --vocab_size 3200 --hidden_size 768 --intermediate_size 3072 --num_hidden_layers 6 --num_attention_heads 12 --hidden_act "gelu" --save_step_freq 200 --sample_size 10000000 --mask_probability 0.15 --short_seq_prob 0.1 --max_steps=300'
    //         sh 'cd examples/nlp/language_modeling && LOSS=$(cat outputs/bert_lm/log_globalrank-0_localrank-0.txt |  grep "Loss" | awk "{print $7}" | tail -n 1| egrep -o "[0-9.]+" ) && echo $LOSS && if [ $(echo "$LOSS > 8.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
    //         sh 'rm -rf examples/nlp/language_modeling/outputs'
    //       }
    //     }
    //   }
    // }

    // stage('ASR processing') {
    //   failFast true
    //   parallel { 
    //     stage('asr_processing') {
    //       steps {
    //         sh './reinstall.sh && cd examples/nlp/asr_postprocessor && CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2  asr_postprocessor.py --data_dir=/home/mrjenkins/TestData/nlp/asr_postprocessor/pred_real --restore_from=/home/mrjenkins/TestData/nlp/asr_postprocessor/bert-base-uncased_decoder.pt --max_steps=50 --batch_size=512'
    //         sh 'cd examples/nlp/asr_postprocessor && WER=$(cat outputs/asr_postprocessor/log_globalrank-0_localrank-0.txt | grep "Validation WER" | tail -n 1 | egrep -o "[0-9.]+" | tail -n 1) && echo $WER && if [ $(echo "$WER > 2.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
    //         sh 'rm -rf examples/nlp/asr_postprocessor/outputs'
    //       }
    //     }
    //   }
    // }

    // stage('Unittests general') {
    //   steps {
    //     sh './reinstall.sh && python -m unittest tests/*.py'
    //   }
    // }


    // stage('Unittests ASR') {
    //   steps {
    //     sh 'python -m unittest tests/asr/*.py'
    //   }
    // }
    // stage('Unittests NLP') {
    //   steps {
    //     sh 'python -m unittest tests/nlp/*.py'
    //   }
    // }
    // stage('Unittests TTS') {
    //   steps {
    //     sh 'python -m unittest tests/tts/*.py'
    //   }
    // }

    // stage('Parallel Stage1') {
    //   failFast true
    //   parallel {
    //     stage('Simplest test') {
    //       steps {
    //         sh 'cd examples/start_here && CUDA_VISIBLE_DEVICES=0 python simplest_example.py'
    //       }
    //     }
    //     stage ('Chatbot test') {
    //       steps {
    //         sh 'cd examples/start_here && CUDA_VISIBLE_DEVICES=1 python chatbot_example.py'
    //       }
    //     }
    //   }
    // }


    // stage('Parallel NLP Examples 1') {
    //   failFast true
    //   parallel {
    //     stage ('Text Classification with BERT Test') {
    //       steps {
    //         sh 'cd examples/nlp/text_classification && CUDA_VISIBLE_DEVICES=0 python text_classification_with_bert.py --num_epochs=1 --max_seq_length=50 --dataset_name=jarvis --data_dir=/home/mrjenkins/TestData/nlp/retail/ --eval_file_prefix=eval --batch_size=10 --num_train_samples=-1 --do_lower_case --shuffle_data --work_dir=outputs'
    //         sh 'rm -rf examples/nlp/text_classification/outputs'
    //       }
    //     }
    //     stage ('Dialogue State Tracking - TRADE - Multi-GPUs') {
    //       steps {
    //         sh 'cd examples/nlp/dialogue_state_tracking && CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2 dialogue_state_tracking_trade.py --batch_size=10 --eval_batch_size=10 --num_train_samples=-1 --num_eval_samples=-1 --num_epochs=1 --dropout=0.2 --eval_file_prefix=test --shuffle_data --num_gpus=2 --lr=0.001 --grad_norm_clip=10 --work_dir=outputs --data_dir=/home/mrjenkins/TestData/nlp/multiwoz2.1'
    //         sh 'rm -rf examples/nlp/dialogue_state_tracking/outputs'
    //       }
    //     }
    //     stage ('GLUE Benchmark Test') {
    //       steps {
    //         sh 'cd examples/nlp/glue_benchmark && CUDA_VISIBLE_DEVICES=1 python glue_benchmark_with_bert.py --data_dir /home/mrjenkins/TestData/nlp/glue_fake/MRPC --work_dir glue_output --save_step_freq -1 --num_epochs 1 --task_name mrpc --batch_size 2'
    //         sh 'rm -rf examples/nlp/glue_benchmark/glue_output'
    //       }
    //     }
    //   }
    // }


    // stage('Parallel NLP Examples 2') {
    //   failFast true
    //   parallel {
    //     stage('Token Classification Training/Inference Test') {
    //       steps {
    //         sh 'cd examples/nlp/token_classification && CUDA_VISIBLE_DEVICES=0 python token_classification.py --data_dir /home/mrjenkins/TestData/nlp/token_classification_punctuation/ --batch_size 2 --num_epochs 1 --save_epoch_freq 1 --work_dir token_classification_output --pretrained_bert_model bert-base-cased'
    //         sh 'cd examples/nlp/token_classification && DATE_F=$(ls token_classification_output/) && CUDA_VISIBLE_DEVICES=0 python token_classification_infer.py --work_dir token_classification_output/$DATE_F/checkpoints/ --labels_dict /home/mrjenkins/TestData/nlp/token_classification_punctuation/label_ids.csv --pretrained_bert_model bert-base-cased'
    //         sh 'rm -rf examples/nlp/token_classification/token_classification_output'
    //       }
    //     }
    //     stage ('Punctuation and Classification Training/Inference Test') {
    //       steps {
    //         sh 'cd examples/nlp/token_classification && CUDA_VISIBLE_DEVICES=1 python punctuation_capitalization.py --data_dir /home/mrjenkins/TestData/nlp/token_classification_punctuation/ --work_dir punctuation_output --save_epoch_freq 1 --num_epochs 1 --save_step_freq -1 --batch_size 2'
    //         sh 'cd examples/nlp/token_classification && DATE_F=$(ls punctuation_output/) && DATA_DIR="/home/mrjenkins/TestData/nlp/token_classification_punctuation" && CUDA_VISIBLE_DEVICES=1 python punctuation_capitalization_infer.py --checkpoints_dir punctuation_output/$DATE_F/checkpoints/ --punct_labels_dict $DATA_DIR/punct_label_ids.csv --capit_labels_dict $DATA_DIR/capit_label_ids.csv'
    //         sh 'rm -rf examples/nlp/token_classification/punctuation_output'
    //       }
    //     }
    //   }
    // }

    // stage('Intent Detection/SLot Tagging Examples - Multi-GPU') {
    //   failFast true
    //     steps {
    //       sh 'cd examples/nlp/intent_detection_slot_tagging && CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2 joint_intent_slot_with_bert.py --num_gpus=2 --num_epochs=1 --max_seq_length=50 --dataset_name=jarvis-retail --data_dir=/home/mrjenkins/TestData/nlp/retail/ --eval_file_prefix=eval --batch_size=10 --num_train_samples=-1 --do_lower_case --shuffle_data --work_dir=outputs'
    //       sh 'cd examples/nlp/intent_detection_slot_tagging && TASK_NAME=$(ls outputs/) && DATE_F=$(ls outputs/$TASK_NAME/) && CHECKPOINT_DIR=outputs/$TASK_NAME/$DATE_F/checkpoints/ && CUDA_VISIBLE_DEVICES=0 python joint_intent_slot_infer.py --work_dir $CHECKPOINT_DIR --eval_file_prefix=eval --dataset_name=jarvis-retail --data_dir=/home/mrjenkins/TestData/nlp/retail/ --batch_size=10'
    //       sh 'cd examples/nlp/intent_detection_slot_tagging && TASK_NAME=$(ls outputs/) && DATE_F=$(ls outputs/$TASK_NAME/) && CHECKPOINT_DIR=outputs/$TASK_NAME/$DATE_F/checkpoints/ && CUDA_VISIBLE_DEVICES=0 python joint_intent_slot_infer_b1.py --data_dir=/home/mrjenkins/TestData/nlp/retail/ --work_dir $CHECKPOINT_DIR --dataset_name=jarvis-retail --query="how much is it?"'
    //       sh 'rm -rf examples/nlp/intent_detection_slot_tagging/outputs'
    //     }
    //   }

    // stage('NMT Example') {
    //   failFast true
    //     steps {
	  //     sh 'cd examples/nlp/neural_machine_translation/ && CUDA_VISIBLE_DEVICES=0 python machine_translation_tutorial.py --max_steps 100'
    //       sh 'rm -rf examples/nlp/neural_machine_translation/outputs'        
    //   }
    // }

    // stage('Parallel Stage Jasper') {
    //   failFast true
    //   parallel {
    //     stage('Jasper AN4 O1') {
    //       steps {
    //         sh 'cd examples/asr && CUDA_VISIBLE_DEVICES=0 python jasper_an4.py --amp_opt_level=O1 --num_epochs=35 --test_after_training --work_dir=O1'
    //       }
    //     }
    //     stage('Jasper AN4 O2') {
    //       steps {
    //         sh 'cd examples/asr && CUDA_VISIBLE_DEVICES=1 python jasper_an4.py --amp_opt_level=O2 --num_epochs=35 --test_after_training --work_dir=O2'
    //       }
    //     }
    //   }
    // }

    // stage('Parallel Stage GAN') {
    //   failFast true
    //   parallel {
    //     stage('GAN O1') {
    //       steps {
    //         sh 'cd examples/image && CUDA_VISIBLE_DEVICES=0 python gan.py --amp_opt_level=O1 --num_epochs=3'
    //       }
    //     }
    //     stage('GAN O2') {
    //       steps {
    //         sh 'cd examples/image && CUDA_VISIBLE_DEVICES=1 python gan.py --amp_opt_level=O2 --num_epochs=3'
    //       }
    //     }
    //   }
    // }

    // stage('Multi-GPU test') {
    //   failFast true
    //   parallel {
    //     stage('Jasper AN4 2 GPUs') {
    //       steps {
    //         sh 'cd examples/asr && CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2 jasper_an4.py --num_epochs=40 --batch_size=24 --work_dir=multi_gpu --test_after_training'
    //       }
    //     }
    //   }
    // }

    // stage('TTS Tests') {
    //   failFast true
    //   steps {
    //     sh 'cd examples/tts && CUDA_VISIBLE_DEVICES=0,1 python -m torch.distributed.launch --nproc_per_node=2 tacotron2.py --max_steps=51 --model_config=configs/tacotron2.yaml --train_dataset=/home/mrjenkins/TestData/an4_dataset/an4_train.json --amp_opt_level=O1 --eval_freq=50'
    //     sh 'cd examples/tts && TTS_CHECKPOINT_DIR=$(ls | grep "Tacotron2") && echo $TTS_CHECKPOINT_DIR && LOSS=$(cat $TTS_CHECKPOINT_DIR/log_globalrank-0_localrank-0.txt | grep -o -E "Loss[ :0-9.]+" | grep -o -E "[0-9.]+" | tail -n 1) && echo $LOSS && if [ $(echo "$LOSS > 3.0" | bc -l) -eq 1 ]; then echo "FAILURE" && exit 1; else echo "SUCCESS"; fi'
    //     // sh 'cd examples/tts && TTS_CHECKPOINT_DIR=$(ls | grep "Tacotron2") && cp ../asr/multi_gpu/checkpoints/* $TTS_CHECKPOINT_DIR/checkpoints'
    //     // sh 'CUDA_VISIBLE_DEVICES=0 python tacotron2_an4_test.py --model_config=configs/tacotron2.yaml --eval_dataset=/home/mrjenkins/TestData/an4_dataset/an4_train.json --jasper_model_config=../asr/configs/jasper_an4.yaml --load_dir=$TTS_CHECKPOINT_DIR/checkpoints'
    //   }
    // }

  }

  post {
    always {
        cleanWs()
    }
  }
}
