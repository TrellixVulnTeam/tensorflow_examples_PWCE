# +
import tensorflow as tf
import tensorflow_datasets as tfds
import tensorflow_hub as hub

import numpy as np
import pickle

import learner_mod
import solution_mod

import inspect


# -

def get_failed_cases(test_cases):
    
    failed_cases = []
    
    for test_case in test_cases:
        name = test_case.get("name")
        got = test_case.get("got")
        expected = test_case.get("expected")

        try:
            if(type(got) == np.ndarray):
                assert np.allclose(got, expected)
            
            elif(type(got) == list):
                for a, b in zip(got, expected):
                    if(np.allclose(a,b) == False):
                        raise
            else:
                assert got == expected
            
        except:
            failed_cases.append({"name": name, "expected": expected, "got": got})
    
    return failed_cases


def Test_map_fn():
    
    with open('sample_image.pkl', 'rb') as f:
        image = pickle.load(f)
    
    label = 1
        
    got = learner_mod.map_fn(image, label)
    expected = solution_mod.map_fn(image, label)
    
    image_volume = expected[0].shape[0] * expected[0].shape[1] * expected[0].shape[2]
    
    test_cases = [
        {
            "name": "function_type_check",
            "got": type(learner_mod.map_fn),
            "expected": type(solution_mod.map_fn)
        },
        {
            "name": "return_type_check",
            "got": type(got),
            "expected": type(expected)
        },
        {
            "name": "image_type_check",
            "got": type(got[0]),
            "expected": type(expected[0])
        },
        {
            "name": "label_type_check",
            "got": type(got[1]),
            "expected": type(expected[1])
        },
        {
            "name": "check_if_resized",
            "got": got[0].shape,
            "expected": expected[0].shape
        },
        {
            "name": "check_if_normalized",
            "got": got[0].numpy().sum() <= image_volume,
            "expected": True
        },
    ]

    failed_cases = get_failed_cases(test_cases)

    return failed_cases, len(test_cases)


def Test_set_adam_optimizer():
    got = learner_mod.set_adam_optimizer()
    expected = solution_mod.set_adam_optimizer()
    
    failed_cases = []
    
    if type(got) != type(expected):
        failed_cases = [{"name": "type_check", 
                         "expected": type(expected), 
                         "got": type(got)}]
        
    return failed_cases, 1 


def Test_set_sparse_cat_crossentropy_loss():
    
    got_train_loss, got_val_loss = learner_mod.set_sparse_cat_crossentropy_loss()
    expected_train_loss, expected_val_loss = solution_mod.set_sparse_cat_crossentropy_loss()

    test_cases = [
        {
            "name": "train_loss_type_check",
            "got": type(got_train_loss),
            "expected": type(expected_train_loss),
        },
        {
            "name": "val_loss_type_check",
            "got": type(got_val_loss),
            "expected": type(expected_val_loss),
        },
    ]

    failed_cases = get_failed_cases(test_cases)

    return failed_cases, len(test_cases)    


def Test_set_sparse_cat_crossentropy_accuracy():
    got_train_accuracy, got_val_accuracy = learner_mod.set_sparse_cat_crossentropy_accuracy()
    expected_train_accuracy, expected_val_accuracy = solution_mod.set_sparse_cat_crossentropy_accuracy()

    test_cases = [
        {
            "name": "train_accuracy_type_check",
            "got": type(got_train_accuracy),
            "expected": type(expected_train_accuracy)
        },
        {
            "name": "val_accuracy_type_check",
            "got": type(got_val_accuracy),
            "expected": type(expected_val_accuracy)
        },
    ]

    failed_cases = get_failed_cases(test_cases)

    return failed_cases, len(test_cases)    
    


def Test_prepare_dataset():
    
    splits, info = tfds.load('horses_or_humans', as_supervised=True, with_info=True, split=['train[:4%]', 'train[99%:]', 'test[:10%]'], data_dir='./data')
    (train_examples, validation_examples, test_examples) = splits
    
    BATCH_SIZE = 10
    NUM_EXAMPLES = len(train_examples)
    
    map_fn = solution_mod.map_fn
    
    got_train_ds, got_valid_ds, got_test_ds = learner_mod.prepare_dataset(train_examples, validation_examples, test_examples, NUM_EXAMPLES, map_fn, BATCH_SIZE)
    expected_train_ds, expected_valid_ds, expected_test_ds = solution_mod.prepare_dataset(train_examples, validation_examples, test_examples, NUM_EXAMPLES, map_fn, BATCH_SIZE)
    
    test_got_image = list(got_train_ds)[4]
    test_expected_image = list(expected_train_ds)[4]
    
    image_volume = test_expected_image[0].shape[1] * test_expected_image[0].shape[2] * test_expected_image[0].shape[3]

    def check_if_shuffled():
        i = 5
        shuffled = False
        
        shuf_train_ds, _, _ = learner_mod.prepare_dataset(train_examples, validation_examples, test_examples, NUM_EXAMPLES, map_fn, BATCH_SIZE)        
        output = list(shuf_train_ds)[0][0].numpy()
        
        while i > 0:
            new_shuf_train_ds, _, _ = learner_mod.prepare_dataset(train_examples, validation_examples, test_examples, NUM_EXAMPLES, map_fn, BATCH_SIZE)
            new_output = list(new_shuf_train_ds)[0][0].numpy()
            
            if not (np.allclose(output, new_output)):
                shuffled = True
                break;
                
        return shuffled
        
    if type(got_train_ds) != type(expected_train_ds):
        failed_cases = [{"name": "type_check", 
                         "expected": type(expected_train_ds), 
                         "got": type(got_train_ds)}]
        
        return failed_cases, 1
    
    else:
        test_cases = [
            {
                "name": "check_if_resized",
                "got": test_got_image[0].shape,
                "expected": test_expected_image[0].shape
            },
            {
                "name": "check_if_normalized",
                "got": test_got_image[0].numpy().sum() <= image_volume,
                "expected": True
            },
            {
                "name": "check_if_shuffled",
                "got": check_if_shuffled(),
                "expected": True
            },
            {
                "name": "check_if_batched",
                "got": got_train_ds._batch_size,
                "expected": expected_train_ds._batch_size
            },
        ]

        failed_cases = get_failed_cases(test_cases)

        return failed_cases, len(test_cases)


def Test_train_one_step():

    MODULE_HANDLE = 'data/resnet_50_feature_vector'
    num_classes = 2
    
    test_model = tf.keras.Sequential([
        hub.KerasLayer(MODULE_HANDLE, input_shape=(224, 224, 3)),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    solution_model = tf.keras.Sequential([
        hub.KerasLayer(MODULE_HANDLE, input_shape=(224, 224, 3)),
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
    
    solution_model.set_weights(test_model.get_weights())
    
    optimizer = solution_mod.set_adam_optimizer()
    
    with open('sample_dataset_image.pkl', 'rb') as f:
        image, label = pickle.load(f)
    
    train_loss, _ = solution_mod.set_sparse_cat_crossentropy_loss()
    train_accuracy, _ = solution_mod.set_sparse_cat_crossentropy_accuracy()
    
    got = learner_mod.train_one_step(test_model, optimizer, image, label, train_loss, train_accuracy)
    expected = solution_mod.train_one_step(solution_model, optimizer, image, label, train_loss, train_accuracy)
    
    if type(got) != type(expected):
        failed_cases = [{"name": "type_check", 
                         "expected": type(expected), 
                         "got": type(got)}]
        
        return failed_cases, 1
    
    else:
        test_cases = [
            {
                "name": "output_check",
                "got": got,
                "expected": expected,
            },
        ]

        failed_cases = get_failed_cases(test_cases)

        return failed_cases, len(test_cases)


def Test_train():
    
    got = inspect.getsource(learner_mod.train).replace(" ", "").replace("\r", "").replace("\n", "")
    
    def search(got_string, pattern):
        found = False
        
        if got_string.find(pattern) > -1:
            found = True
        
        return found
    
    loss_pattern = "@tf.functiondeftrain(model,optimizer,epochs,device,train_ds,train_loss,train_accuracy,valid_ds,val_loss,val_accuracy):step=0loss=0.0forepochinrange(epochs):forx,yintrain_ds:step+=1withtf.device(device_name=device):###STARTCODEHERE####Runonetrainingstepbypassingappropriatemodelparameters#requiredbythefunctionandfinallygetthelosstoreporttheresultsloss=train_one_step(model,optimizer,x,y,train_loss)"
    
    tf_print_pattern1 = "@tf.functiondeftrain(model,optimizer,epochs,device,train_ds,train_loss,train_accuracy,valid_ds,val_loss,val_accuracy):step=0loss=0.0forepochinrange(epochs):forx,yintrain_ds:step+=1withtf.device(device_name=device):###STARTCODEHERE####Runonetrainingstepbypassingappropriatemodelparameters#requiredbythefunctionandfinallygetthelosstoreporttheresultsloss=train_one_step(model,optimizer,x,y,train_loss)#Relyonreliabledebuggingfunctionsliketf.printtoreportyourresults.#Printthetrainingstepnumber,lossandaccuracytf.print"
    
    step_pattern = "@tf.functiondeftrain(model,optimizer,epochs,device,train_ds,train_loss,train_accuracy,valid_ds,val_loss,val_accuracy):step=0loss=0.0forepochinrange(epochs):forx,yintrain_ds:step+=1withtf.device(device_name=device):###STARTCODEHERE####Runonetrainingstepbypassingappropriatemodelparameters#requiredbythefunctionandfinallygetthelosstoreporttheresultsloss=train_one_step(model,optimizer,x,y,train_loss)#Relyonreliabledebuggingfunctionsliketf.printtoreportyourresults.#Printthetrainingstepnumber,lossandaccuracytf.print('Step',step"
    
    train_loss_pattern = "@tf.functiondeftrain(model,optimizer,epochs,device,train_ds,train_loss,train_accuracy,valid_ds,val_loss,val_accuracy):step=0loss=0.0forepochinrange(epochs):forx,yintrain_ds:step+=1withtf.device(device_name=device):###STARTCODEHERE####Runonetrainingstepbypassingappropriatemodelparameters#requiredbythefunctionandfinallygetthelosstoreporttheresultsloss=train_one_step(model,optimizer,x,y,train_loss)#Relyonreliabledebuggingfunctionsliketf.printtoreportyourresults.#Printthetrainingstepnumber,lossandaccuracytf.print('Step',step,':trainloss',loss,"
    
    train_accuracy_pattern = "@tf.functiondeftrain(model,optimizer,epochs,device,train_ds,train_loss,train_accuracy,valid_ds,val_loss,val_accuracy):step=0loss=0.0forepochinrange(epochs):forx,yintrain_ds:step+=1withtf.device(device_name=device):###STARTCODEHERE####Runonetrainingstepbypassingappropriatemodelparameters#requiredbythefunctionandfinallygetthelosstoreporttheresultsloss=train_one_step(model,optimizer,x,y,train_loss)#Relyonreliabledebuggingfunctionsliketf.printtoreportyourresults.#Printthetrainingstepnumber,lossandaccuracytf.print('Step',step,':trainloss',loss,';trainaccuracy',train_accuracy.result())"
    
    tf_print_pattern2 = "###STARTCODEHERE####Printthevalidationlossandaccuracytf.print("
    
    val_loss_pattern = "###STARTCODEHERE####Printthevalidationlossandaccuracytf.print('valloss',loss,"
    
    val_accuracy_pattern = "###STARTCODEHERE####Printthevalidationlossandaccuracytf.print('valloss',loss,';valaccuracy',val_accuracy.result())"
    
    test_cases = [
        {
            "name": "function_type_check",
            "got": type(learner_mod.train),
            "expected": type(solution_mod.train)
        },
        {
            "name": "loss_pattern_check",
            "got": search(got, loss_pattern),
            "expected": True
        },
        {
            "name": "tfprint1_pattern_check",
            "got": search(got, tf_print_pattern1),
            "expected": True
        },
        {
            "name": "step_pattern_check",
            "got": search(got, step_pattern),
            "expected": True
        },
        {
            "name": "train_loss_pattern_check",
            "got": search(got, train_loss_pattern),
            "expected": True
        },
        {
            "name": "train_accuracy_pattern_check",
            "got": search(got, train_accuracy_pattern),
            "expected": True
        },
        {
            "name": "tfprint2_pattern_check",
            "got": search(got, tf_print_pattern2),
            "expected": True
        },
        {
            "name": "val_loss_pattern_check",
            "got": search(got, val_loss_pattern),
            "expected": True
        },
        {
            "name": "val_accuracy_pattern_check",
            "got": search(got, val_accuracy_pattern),
            "expected": True
        },
    ]
    
    failed_cases = get_failed_cases(test_cases)

    return failed_cases, len(test_cases)    
